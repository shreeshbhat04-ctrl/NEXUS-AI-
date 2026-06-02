import X2CTViewer from "../components/imaging/X2CTViewer";

export default function X2CTViewerScreen() {
  return (
    <div style={{ minHeight: 'calc(100vh - 8rem)', padding: '1rem 0' }}>
      <X2CTViewer />
    </div>
  );
}
