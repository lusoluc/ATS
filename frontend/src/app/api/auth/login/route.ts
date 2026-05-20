import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { password, role } = body;

    // Demo-Passwort (kann später durch echte DB-Prüfung ersetzt werden)
    const DEMO_PASSWORD = process.env.DEMO_PASSWORD || "securats2024";

    if (password !== DEMO_PASSWORD) {
      return NextResponse.json({ error: "Falsches Passwort" }, { status: 401 });
    }

    const response = NextResponse.json({ success: true, role });
    
    // Sicheres HTTP-Only Cookie setzen
    response.cookies.set('securats_auth_role', role, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 // 1 Tag gültig
    });

    return response;
  } catch (error) {
    return NextResponse.json({ error: "Interner Server Fehler" }, { status: 500 });
  }
}
