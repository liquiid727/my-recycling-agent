import { useEffect, useMemo, useState } from "react";

import { getExperienceContent, saveExperienceContent } from "./api";
import type { ExperienceContent } from "../experience/api";

export function useAdminExperienceContent() {
  const [content, setContent] = useState<ExperienceContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void getExperienceContent()
      .then((payload) => {
        if (!active) return;
        setContent(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("内容后台暂时不可用。");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function persist(nextContent: ExperienceContent) {
    setSaving(true);
    setError(null);
    try {
      const saved = await saveExperienceContent(nextContent);
      setContent(saved);
    } catch {
      setError("内容保存失败，请稍后重试。");
    } finally {
      setSaving(false);
    }
  }

  return useMemo(
    () => ({ content, loading, saving, error, persist, setContent }),
    [content, loading, saving, error],
  );
}
