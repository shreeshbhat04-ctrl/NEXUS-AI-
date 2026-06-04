import { useEffect, useEffectEvent, useRef, useState } from 'react';
import {
  connectFinanceWorkflowStream,
  fetchFinanceSummary,
  recordFinanceConsent,
  submitFinanceApplication,
  uploadFinanceBill,
  type FinanceLoanOffer,
  type FinanceWorkflowEvent,
  type FinanceWorkflowSnapshot,
  type FinanceWorkflowStep,
} from '../../shared/lib/api';

function uniqueEvents(events: FinanceWorkflowEvent[]) {
  const seen = new Set<string>();
  return events.filter((event) => {
    const key = `${event.step}:${event.timestamp}:${event.message}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export function useFinancialWorkflow(patientId: number) {
  const [currentStep, setCurrentStep] = useState<FinanceWorkflowStep>('idle');
  const [snapshot, setSnapshot] = useState<FinanceWorkflowSnapshot | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [billId, setBillId] = useState<string | null>(null);
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('Upload a hospital bill PDF to begin the audit.');
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [events, setEvents] = useState<FinanceWorkflowEvent[]>([]);

  const latestFileRef = useRef<File | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const consentIdRef = useRef<string | null>(null);
  const pdfUrlRef = useRef<string | null>(null);

  const closeStream = () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
  };

  const updatePdfUrl = (nextUrl: string | null) => {
    if (pdfUrlRef.current) {
      URL.revokeObjectURL(pdfUrlRef.current);
    }
    pdfUrlRef.current = nextUrl;
    setPdfUrl(nextUrl);
  };

  const applySnapshot = useEffectEvent((nextSnapshot: FinanceWorkflowSnapshot) => {
    setSnapshot(nextSnapshot);
    setSessionId(nextSnapshot.session_id);
    setBillId(nextSnapshot.bill_id);
    setCurrentStep(nextSnapshot.current_step);
    setStatusMessage(nextSnapshot.status_message);
    setEvents(uniqueEvents(nextSnapshot.events));

    setSelectedOfferId((current) => {
      if (current && nextSnapshot.loan_offers.some((offer) => offer.id === current)) {
        return current;
      }
      return nextSnapshot.selected_offer_id
        ?? nextSnapshot.loan_offers.find((offer) => offer.is_top_pick)?.id
        ?? nextSnapshot.loan_offers[0]?.id
        ?? null;
    });
  });

  const refreshSummary = useEffectEvent(async (targetBillId?: string | null) => {
    if (!targetBillId) {
      return;
    }
    const nextSnapshot = await fetchFinanceSummary(targetBillId);
    applySnapshot(nextSnapshot);
  });

  const handleWorkflowEvent = useEffectEvent((event: FinanceWorkflowEvent) => {
    setEvents((current) => uniqueEvents([...current, event]));
    if (event.step === 'submitted') {
      void refreshSummary(billId);
    }
  });

  const openWorkflowStream = useEffectEvent((targetSessionId: string) => {
    closeStream();
    eventSourceRef.current = connectFinanceWorkflowStream(
      targetSessionId,
      handleWorkflowEvent,
      () => {
        closeStream();
      },
    );
  });

  const uploadBill = async (file: File) => {
    latestFileRef.current = file;
    setError(null);
    setIsUploading(true);
    setUploadProgress(15);
    setCurrentStep('uploading');
    setStatusMessage('Sending your bill into the finance workflow.');

    try {
      updatePdfUrl(URL.createObjectURL(file));
      const response = await uploadFinanceBill(patientId, file);
      setUploadProgress(100);
      applySnapshot(response.summary);
      openWorkflowStream(response.session_id);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Unable to upload this bill right now.');
    } finally {
      setIsUploading(false);
    }
  };

  const selectOffer = (offerId: string) => {
    setSelectedOfferId(offerId);
    setStatusMessage('Selected an offer. Review the consent terms before submitting.');
  };

  const submitApplication = async () => {
    if (!billId || !selectedOfferId) {
      setError('Select a financing offer before continuing.');
      return false;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const consent = await recordFinanceConsent(patientId, billId, selectedOfferId);
      consentIdRef.current = consent.consent_id;
      const submission = await submitFinanceApplication(patientId, billId, selectedOfferId, consent.consent_id);

      setCurrentStep('submitted');
      setStatusMessage('Your financing application has been submitted.');
      setSnapshot((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          current_step: 'submitted',
          status_message: 'Your financing application has been submitted.',
          consent_status: 'granted',
          selected_offer_id: selectedOfferId,
          application_id: submission.submission_id,
        };
      });
      return true;
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Unable to submit the application.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const retryCurrentStep = async () => {
    setError(null);
    if (latestFileRef.current && !billId) {
      await uploadBill(latestFileRef.current);
      return;
    }
    await refreshSummary(billId);
  };

  const reset = () => {
    closeStream();
    setSnapshot(null);
    setSessionId(null);
    setBillId(null);
    setSelectedOfferId(null);
    setCurrentStep('idle');
    setStatusMessage('Upload a hospital bill PDF to begin the audit.');
    setError(null);
    setIsUploading(false);
    setIsSubmitting(false);
    setUploadProgress(0);
    setEvents([]);
    consentIdRef.current = null;
    latestFileRef.current = null;
    updatePdfUrl(null);
  };

  useEffect(() => {
    return () => {
      closeStream();
      if (pdfUrlRef.current) {
        URL.revokeObjectURL(pdfUrlRef.current);
      }
    };
  }, []);

  const selectedOffer = snapshot?.loan_offers.find((offer) => offer.id === selectedOfferId) ?? null;
  const isProcessing = isUploading || isSubmitting;

  return {
    currentStep,
    statusMessage,
    isProcessing,
    isUploading,
    isSubmitting,
    uploadProgress,
    error,
    sessionId,
    billId,
    pdfUrl,
    events,
    snapshot,
    auditResult: snapshot?.audit_result ?? null,
    gapResult: snapshot?.gap_result ?? null,
    loanOffers: snapshot?.loan_offers ?? [],
    policyCitations: snapshot?.policy_citations ?? [],
    selectedOffer,
    selectedOfferId,
    applicationId: snapshot?.application_id ?? null,
    consentStatus: snapshot?.consent_status ?? 'pending',
    uploadBill,
    selectOffer,
    submitApplication,
    retryCurrentStep,
    reset,
  };
}

export type { FinanceLoanOffer, FinanceWorkflowSnapshot, FinanceWorkflowStep };
