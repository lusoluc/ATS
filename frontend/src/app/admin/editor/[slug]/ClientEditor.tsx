"use client";

import { Puck } from "@measured/puck";
import "@measured/puck/puck.css";
import { config } from "../../../../puck.config";

export function ClientEditor({ initialData, slug }: { initialData: any, slug: string }) {
  const save = async (data: any) => {
    try {
      const res = await fetch(`/api/cms/pages/${slug}/puck`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) alert("Fehler beim Speichern");
      else alert("Erfolgreich gespeichert!");
    } catch (e) {
      alert("Fehler beim Speichern");
    }
  };

  return <Puck config={config} data={initialData} onPublish={save} />;
}
