import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const roleCookie = request.cookies.get('securats_auth_role');

  // Schütze den /admin Bereich
  if (request.nextUrl.pathname.startsWith('/admin')) {
    if (!roleCookie) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  // Schütze die internen CMS API Routen
  if (request.nextUrl.pathname.startsWith('/api/cms')) {
    if (!roleCookie) {
      return NextResponse.json({ error: 'Nicht autorisiert. Bitte einloggen.' }, { status: 401 });
    }
  }

  return NextResponse.next();
}

// Konfiguriere auf welche Pfade die Middleware angewendet wird
export const config = {
  matcher: ['/admin/:path*', '/api/cms/:path*'],
};
