export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

export async function GET() {
  try {
    const [categories, locations] = await Promise.all([
      prisma.jobFamily.findMany({
        select: { id: true, name: true },
        orderBy: { name: 'asc' }
      }),
      prisma.location.findMany({
        select: { id: true, city: true, name: true },
        orderBy: { city: 'asc' }
      })
    ]);

    // Return unique locations by city or name
    const uniqueLocations = Array.from(new Map(locations.map(loc => [loc.city || loc.name, loc])).values());

    return NextResponse.json({ categories, locations: uniqueLocations });
  } catch (error) {
    console.error('Failed to fetch job alert options:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
