export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function geocode(name: string): Promise<{ lat: number; lng: number } | null> {
  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(name)},Deutschland&format=json&limit=1&countrycodes=de`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Enterprise-Karriereplattform/1.0' },
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    if (!data || data.length === 0) return null;
    return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
  } catch { return null; }
}

export async function GET() {
  try {
    const locations = await prisma.location.findMany({ orderBy: { name: 'asc' } });
    return NextResponse.json({ locations });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const { name, city, address } = await req.json();
    if (!name) return NextResponse.json({ error: 'Name erforderlich' }, { status: 400 });
    const existing = await prisma.location.findFirst({ where: { name } });
    if (existing) return NextResponse.json({ error: 'Standort existiert bereits' }, { status: 409 });

    // Automatisches Geocoding
    const coords = await geocode(name);

    const location = await prisma.location.create({
      data: {
        name,
        city: city || name,
        address: address || '',
        lat: coords?.lat ?? null,
        lng: coords?.lng ?? null,
      },
    });
    return NextResponse.json({ location, geocoded: coords !== null }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const { id, name, archived } = await req.json();
    if (!id) return NextResponse.json({ error: 'ID erforderlich' }, { status: 400 });
    
    const updateData: any = {};
    
    if (name !== undefined) {
      updateData.name = name;
      updateData.city = name;
      // Automatisches Geocoding bei Namensänderung
      const coords = await geocode(name);
      if (coords) {
        updateData.lat = coords.lat;
        updateData.lng = coords.lng;
      }
    }
    
    if (archived !== undefined) {
      updateData.archived = archived;
    }
    
    const location = await prisma.location.update({ 
      where: { id }, 
      data: updateData 
    });
    return NextResponse.json({ location, geocoded: updateData.lat !== undefined });
  } catch (e: any) {
    if (e.code === 'P2025') return NextResponse.json({ error: 'Standort nicht gefunden' }, { status: 404 });
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });
    await prisma.location.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (e: any) {
    if (e.code === 'P2003') {
      return NextResponse.json({ error: 'Kann nicht gelöscht werden: Es existieren noch Stellenangebote für diesen Standort.' }, { status: 409 });
    }
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
