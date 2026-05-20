export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Haversine-Formel: Distanz zwischen zwei Koordinaten in km
function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
    Math.cos((lat2 * Math.PI) / 180) *
    Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Geocoding via OpenStreetMap Nominatim (kostenlos, kein API-Key)
async function geocode(query: string): Promise<{ lat: number; lng: number; displayName: string } | null> {
  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)},Deutschland&format=json&limit=1&countrycodes=de`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Enterprise-Karriereplattform/1.0 karriere@Enterprise.de' },
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    if (!data || data.length === 0) return null;
    return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon), displayName: data[0].display_name };
  } catch {
    return null;
  }
}

// GET /api/public/jobs?q=&locationId=&categoryId=&searchLocation=&radiusKm=
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const q            = searchParams.get('q') || '';
    const locationId   = searchParams.get('locationId') || '';
    const categoryId   = searchParams.get('categoryId') || '';
    const searchLoc    = searchParams.get('searchLocation') || ''; // Freitext-Ort für Umkreis
    const radiusKm     = parseFloat(searchParams.get('radiusKm') || '50');

    // Alle veröffentlichten Jobs laden
    let jobs = await prisma.jobPosting.findMany({
      where: {
        workflowState: { name: 'published' },
        ...(locationId && { locationId }),
        ...(categoryId && { jobFamilyId: categoryId }),
      },
      include: { facility: true, location: true, jobFamily: true, workflowState: true },
      orderBy: { createdAt: 'desc' },
    });

    // In-Memory Filter für Stichwort (da SQLite case-insensitive in Prisma nicht unterstützt)
    if (q) {
      const qLower = q.toLowerCase();
      jobs = jobs.filter(job => 
        job.title.toLowerCase().includes(qLower) || 
        (job.description && job.description.toLowerCase().includes(qLower)) ||
        (job.jobFamily && job.jobFamily.name.toLowerCase().includes(qLower))
      );
    }

    // Umkreissuche: Wenn searchLocation gesetzt, geocodieren und filtern
    let geocodeResult: { lat: number; lng: number; displayName: string } | null = null;
    if (searchLoc.trim()) {
      geocodeResult = await geocode(searchLoc.trim());
      if (geocodeResult) {
        const { lat: sLat, lng: sLng } = geocodeResult;
        jobs = jobs.filter(job => {
          const loc = job.location as any;
          if (loc.lat == null || loc.lng == null) return true; // Standorte ohne Koordinaten: immer anzeigen
          const dist = haversineKm(sLat, sLng, loc.lat, loc.lng);
          return dist <= radiusKm;
        });
        // Distanz anhängen (für Sortierung/Anzeige)
        jobs = (jobs as any[]).map(job => {
          const loc = job.location as any;
          if (loc.lat == null || loc.lng == null) return { ...job, distanceKm: null };
          return { ...job, distanceKm: Math.round(haversineKm(sLat, sLng, loc.lat, loc.lng)) };
        });
        // Nach Distanz sortieren
        (jobs as any[]).sort((a, b) => (a.distanceKm ?? 999) - (b.distanceKm ?? 999));
      }
    }

    return NextResponse.json({ jobs, geocodeResult, totalFound: jobs.length });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
