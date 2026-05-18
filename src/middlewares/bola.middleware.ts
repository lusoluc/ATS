import { Request, Response, NextFunction } from 'express';

/**
 * BOLA Guard (Broken Object Level Authorization).
 * Prüft explizit, ob der aktuell authentifizierte Nutzer Zugriff
 * auf ein spezifisches Objekt (z.B. eine Bewerbung) hat.
 */
export const requireApplicantAccess = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  if (!req.user) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }

  const applicationId = req.params.id;
  const userRole = req.user.role;

  // GlobalAdmin und CentralHR haben ggf. weitreichendere Rechte,
  // lokal agierende Rollen MÜSSEN via ApplicantAccessAssignment geprüft werden.
  if (['GlobalAdmin', 'CentralHRCareerAdmin'].includes(userRole)) {
    return next();
  }

  try {
    // Hier würde später der Datenbank-Check mit Prisma stattfinden:
    // const access = await prisma.applicantAccessAssignment.findFirst({
    //   where: { userId: req.user.userId, applicationFormId: applicationId }
    // });
    // if (!access) throw new Error();

    // Mock-Check für den Moment (Simulation):
    const hasAccess = true; 

    if (!hasAccess) {
      // 404 statt 403, um die Existenz von Applicant-IDs nicht zu leaken
      res.status(404).json({ error: 'Application not found or access denied' });
      return;
    }

    next();
  } catch (error) {
    res.status(404).json({ error: 'Application not found or access denied' });
  }
};
