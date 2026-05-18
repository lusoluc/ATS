import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    const { baseUrl, clientId, clientSecret, companyId } = data;

    // Simulate validation
    if (!baseUrl || !baseUrl.startsWith('https://')) {
      return NextResponse.json(
        { success: false, error: 'Die Base-URL muss mit https:// beginnen.' },
        { status: 400 }
      );
    }
    if (!companyId) {
      return NextResponse.json(
        { success: false, error: 'Company ID fehlt.' },
        { status: 400 }
      );
    }
    if (!clientId || !clientSecret) {
      return NextResponse.json(
        { success: false, error: 'Client ID oder Client Secret fehlen.' },
        { status: 401 }
      );
    }

    // Mock an API Ping
    // In a real scenario, we would make a fetch() request to the SAP OData API
    await new Promise((resolve) => setTimeout(resolve, 800));

    if (clientSecret === 'wrong') {
       return NextResponse.json(
        { success: false, error: 'Authentifizierung fehlgeschlagen: Invalid Client Secret' },
        { status: 401 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Verbindung erfolgreich! SAP OData API ist erreichbar.',
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
