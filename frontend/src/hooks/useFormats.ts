import { useEffect, useState } from 'react';

interface FormatsResponse {
  input_formats: string[];
  output_formats: string[];
  notes?: Record<string, string>;
}

interface FormatsAPI {
  getFormats: () => Promise<FormatsResponse>;
}

/**
 * Fetches supported formats from the backend /formats endpoint, falling back
 * to a static list when the API is unavailable. Gives the backend authority
 * over which formats are supported so the frontend doesn't drift out of sync.
 */
export function useFormats(api: FormatsAPI, fallback: string[]) {
  const [outputFormats, setOutputFormats] = useState<string[]>(fallback);
  const [inputFormats, setInputFormats] = useState<string[]>(fallback);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState<Record<string, string> | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    api
      .getFormats()
      .then((res) => {
        if (cancelled) return;
        if (res.output_formats?.length) setOutputFormats(res.output_formats);
        if (res.input_formats?.length) setInputFormats(res.input_formats);
        setNotes(res.notes);
      })
      .catch(() => {
        // Backend unavailable — fallback already set, stay silent.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api]);

  return { inputFormats, outputFormats, notes, loading };
}
