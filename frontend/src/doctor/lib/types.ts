export type RichOutput = {
  text?: string;
  logs?: {
    stdout?: string[];
    stderr?: string[];
  };
  results?: Array<{
    png?: string;
    jpeg?: string;
    svg?: string;
    html?: string;
  }>;
  error?: {
    name?: string;
    value?: string;
    traceback?: string;
  };
};

export type CellData = {
  id: string;
  code: string;
  output: string | RichOutput | null;
  errors: string | null;
  isLoading: boolean;
  agentResponse: string | null;
};
