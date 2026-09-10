"use client";

import { useEffect, useState } from "react";
import { getUser, logout, type User } from "@/lib/auth";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const u = getUser();
    setUser(u);
    setDisplayName(localStorage.getItem("displayName") || u?.username || "");
    setEmailNotifications(localStorage.getItem("pref_emailNotifications") === "true");
    setAutoSave(localStorage.getItem("pref_autoSave") !== "false"); // default on
  }, []);

  const handleSave = () => {
    localStorage.setItem("displayName", displayName);
    localStorage.setItem("pref_emailNotifications", String(emailNotifications));
    localStorage.setItem("pref_autoSave", String(autoSave));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleDelete = () => {
    const ok = window.confirm(
      "This will sign you out and clear your local session on this device. Continue?"
    );
    if (ok) logout();
  };

  return (
    <div className="max-w-4xl mx-auto animate-page-in">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400">Manage your account and preferences</p>
        </div>

        <div className="space-y-6">
          {/* Profile Section */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Profile</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Your name"
                  className="inp focus-ring"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                  <div className="inp bg-slate-900/30 text-slate-400 cursor-not-allowed">
                    {user?.username || "—"}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">College</label>
                  <div className="inp bg-slate-900/30 text-slate-400 cursor-not-allowed">
                    {user?.college || "—"}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Role</label>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-500/30 capitalize">
                  {user?.role || "student"}
                </span>
              </div>
            </div>
          </div>

          {/* Preferences */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Preferences</h2>
            <div className="space-y-5">
              <ToggleRow
                title="Email Notifications"
                subtitle="Receive interview reminders"
                checked={emailNotifications}
                onChange={setEmailNotifications}
              />
              <ToggleRow
                title="Auto-save Answers"
                subtitle="Save answers automatically during interviews"
                checked={autoSave}
                onChange={setAutoSave}
              />
            </div>
          </div>

          {/* Save bar */}
          <div className="flex items-center gap-3">
            <button onClick={handleSave} className="btn-primary btn-press">
              Save Changes
            </button>
            {saved && (
              <span className="text-sm text-emerald-400 animate-content-reveal">✓ Saved</span>
            )}
          </div>

          {/* Danger Zone */}
          <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-6">
            <h2 className="text-lg font-bold text-red-300 mb-1">Danger Zone</h2>
            <p className="text-sm text-gray-400 mb-4">
              Signs you out and clears your saved session on this device.
            </p>
            <button
              onClick={handleDelete}
              className="px-6 py-3 bg-red-600/90 hover:bg-red-600 text-white font-semibold rounded-xl transition-colors btn-press"
            >
              Sign Out &amp; Clear Session
            </button>
          </div>
        </div>
      </div>
  );
}

function ToggleRow({
  title,
  subtitle,
  checked,
  onChange,
}: {
  title: string;
  subtitle: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-white">{title}</p>
        <p className="text-sm text-gray-400">{subtitle}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-12 h-6 rounded-full transition-colors duration-200 focus-ring ${
          checked ? "bg-blue-600" : "bg-slate-600"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
            checked ? "translate-x-6" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}
