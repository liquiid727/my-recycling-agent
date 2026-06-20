import { useEffect, useMemo, useState } from "react";

import { getLifestyleProfile, saveLifestyleProfile, type LifestyleProfile } from "./api";

export function useLifestyleProfile() {
  const [profile, setProfile] = useState<LifestyleProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let active = true;
    void getLifestyleProfile()
      .then((payload) => {
        if (!active) return;
        setProfile(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError("偏好读取失败，请稍后再试。");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function persist(nextProfile: LifestyleProfile) {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const savedProfile = await saveLifestyleProfile(nextProfile);
      setProfile(savedProfile);
      setSaved(true);
    } catch {
      setError("偏好保存失败，请稍后重试。");
    } finally {
      setSaving(false);
    }
  }

  return useMemo(
    () => ({ profile, loading, saving, error, saved, persist }),
    [profile, loading, saving, error, saved],
  );
}
