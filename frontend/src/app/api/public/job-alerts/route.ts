import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
import crypto from 'crypto';

export async function POST(req: Request) {
  try {
    const data = await req.json();
    const { email, globalAlert, categories, locations, radiusKm } = data;

    if (!email) {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 });
    }

    const existingSub = await prisma.jobAlertSubscription.findUnique({
      where: { email }
    });

    const newConfToken = crypto.randomBytes(32).toString('hex');
    const newMgmtToken = existingSub?.managementToken || crypto.randomBytes(32).toString('hex');

    if (!existingSub) {
      // Create new PENDING subscription
      await prisma.jobAlertSubscription.create({
        data: {
          email, 
          status: 'PENDING', 
          globalAlert: globalAlert || false, 
          categories: JSON.stringify(categories || []), 
          locations: JSON.stringify(locations || []), 
          radiusKm: radiusKm ? parseInt(radiusKm) : null,
          confirmationToken: newConfToken, 
          managementToken: newMgmtToken
        }
      });
      // TODO: Send actual DOI email here (e.g. using nodemailer + compiled template)
      console.log(`Job Alert Subscription Created for ${email}. DOI token: ${newConfToken}`);
      return NextResponse.json({ message: 'Aktivierungs-E-Mail wurde gesendet.' }, { status: 201 });
    }

    if (existingSub.status === 'ACTIVE') {
      // Upsert filtering preferences
      await prisma.jobAlertSubscription.update({
        where: { email },
        data: { 
          globalAlert: globalAlert || false, 
          categories: JSON.stringify(categories || []), 
          locations: JSON.stringify(locations || []), 
          radiusKm: radiusKm ? parseInt(radiusKm) : null 
        }
      });
      return NextResponse.json({ message: 'Ihre Präferenzen wurden erfolgreich aktualisiert.' });
    }

    if (existingSub.status === 'PENDING') {
      // Resend confirmation token without creating duplicate row
      await prisma.jobAlertSubscription.update({
        where: { email },
        data: { confirmationToken: newConfToken }
      });
      return NextResponse.json({ message: 'Aktivierungs-E-Mail wurde erneut gesendet.' });
    }

    if (existingSub.status === 'INACTIVE') {
      // Flip to PENDING and trigger new DOI
      await prisma.jobAlertSubscription.update({
        where: { email },
        data: {
          status: 'PENDING', 
          globalAlert: globalAlert || false, 
          categories: JSON.stringify(categories || []), 
          locations: JSON.stringify(locations || []), 
          radiusKm: radiusKm ? parseInt(radiusKm) : null,
          confirmationToken: newConfToken
        }
      });
      return NextResponse.json({ message: 'Aktivierungs-E-Mail wurde gesendet.' });
    }

    return NextResponse.json({ message: 'Processed successfully.' });
  } catch (error) {
    console.error('Job alert subscription error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
