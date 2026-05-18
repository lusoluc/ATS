export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Hilfsfunktion zum Escapen von XML
const escapeXml = (unsafe: string) => {
    return unsafe.replace(/[<>&'"]/g, (c) => {
        switch (c) {
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '&': return '&amp;';
            case '\'': return '&apos;';
            case '"': return '&quot;';
            default: return c;
        }
    });
};

export async function GET() {
    try {
        const jobs = await prisma.jobPosting.findMany({
            where: { workflowState: { name: 'published' } },
            include: {
                facility: true,
                location: true,
                organization: true,
                contactPerson: true
            }
        });

        // Supplier-ID & Co. aus den GlobalSettings (Stammdaten)
        const settings = await prisma.systemSetting.findMany({
            where: { key: { in: ['ba_supplier_id', 'ba_hiring_org_id'] } }
        });
        
        const supplierId = settings.find(s => s.key === 'ba_supplier_id')?.value || "V000000000"; 
        const hiringOrgId = settings.find(s => s.key === 'ba_hiring_org_id')?.value || "A000000000";

        let xml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n`;
        xml += `<HRBAXMLJobPositionPosting>\n`;
        xml += `    <Header>\n`;
        xml += `        <SupplierId>${supplierId}</SupplierId>\n`;
        xml += `        <Timestamp>${new Date().toISOString()}</Timestamp>\n`;
        xml += `        <Amount>${jobs.length}</Amount>\n`;
        xml += `        <TypeOfLoad>F</TypeOfLoad>\n`; // F = Full Load
        xml += `    </Header>\n`;
        xml += `    <Data>\n`;

        for (const job of jobs) {
            const orgName = escapeXml(job.organization.name);
            const title = escapeXml(job.title);
            const desc = escapeXml(job.description || title);
            
            xml += `        <JobPositionPosting>\n`;
            xml += `            <JobPositionPostingId>${job.id}</JobPositionPostingId>\n`;
            
            // Arbeitgeber Infos
            xml += `            <HiringOrg>\n`;
            xml += `                <HiringOrgName>${orgName}</HiringOrgName>\n`;
            xml += `                <HiringOrgId>${hiringOrgId}</HiringOrgId>\n`;
            xml += `                <Contact>\n`;
            xml += `                    <Salutation>1</Salutation>\n`;
            xml += `                    <GivenName>${escapeXml(job.contactPerson?.firstName || 'HR')}</GivenName>\n`;
            xml += `                    <FamilyName>${escapeXml(job.contactPerson?.lastName || 'Team')}</FamilyName>\n`;
            xml += `                </Contact>\n`;
            xml += `            </HiringOrg>\n`;

            // Metadaten zum Posting
            xml += `            <PostDetail>\n`;
            xml += `                <LastModificationDate>${job.updatedAt.toISOString()}</LastModificationDate>\n`;
            xml += `                <Status>1</Status>\n`; // 1 = Active
            xml += `                <Action>1</Action>\n`; // 1 = Create/Update
            xml += `                <SupplierId>${supplierId}</SupplierId>\n`;
            xml += `                <SupplierName>${orgName}</SupplierName>\n`;
            xml += `                <SupervisionDesired>1</SupervisionDesired>\n`; // Betreuung durch Arbeitsagentur gewünscht
            xml += `            </PostDetail>\n`;

            // Job Details
            xml += `            <JobPositionInformation>\n`;
            xml += `                <JobPositionTitle>\n`;
            xml += `                    <TitleCode>00000</TitleCode>\n`; // Müsste auf BA-Katalog gemappt werden (KldB 2010)
            xml += `                </JobPositionTitle>\n`;
            xml += `                <JobPositionTitleDescription>${title}</JobPositionTitleDescription>\n`;
            xml += `                <JobOfferType>1</JobOfferType>\n`; // 1 = Arbeitsplatz
            xml += `                <SocialInsurance>1</SocialInsurance>\n`; // Sozialversicherungspflichtig
            xml += `                <Objective>${desc.substring(0, 9999)}</Objective>\n`;
            xml += `                <JobPositionDescription>\n`;
            xml += `                    <JobPositionLocation>\n`;
            xml += `                        <Location>\n`;
            xml += `                            <CountryCode>DE</CountryCode>\n`;
            xml += `                            <PostalCode>${escapeXml(job.location.postalCode || '00000')}</PostalCode>\n`;
            xml += `                            <Municipality>${escapeXml(job.location.city || 'Unbekannt')}</Municipality>\n`;
            xml += `                            <StreetName>${escapeXml(job.location.address || '')}</StreetName>\n`;
            xml += `                        </Location>\n`;
            xml += `                    </JobPositionLocation>\n`;
            xml += `                </JobPositionDescription>\n`;
            xml += `                <JobPositionRequirements>\n`;
            xml += `                    <ProfessionalExperience>1</ProfessionalExperience>\n`; // 1 = Ohne Berufserfahrung, 2 = Mit, ...
            xml += `                </JobPositionRequirements>\n`;
            xml += `                <NumberToFill>1</NumberToFill>\n`;
            xml += `            </JobPositionInformation>\n`;
            
            xml += `        </JobPositionPosting>\n`;
        }

        xml += `    </Data>\n`;
        xml += `</HRBAXMLJobPositionPosting>`;

        return new NextResponse(xml, {
            headers: {
                'Content-Type': 'application/xml; charset=utf-8',
                // Dateiname für den Download
                'Content-Disposition': 'attachment; filename="hr-ba-xml-export.xml"'
            }
        });

    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
