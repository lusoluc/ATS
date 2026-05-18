import { Request, Response, NextFunction } from 'express';

/**
 * Middleware zur rollenbasierten Zugriffskontrolle (RBAC).
 * Stellt sicher, dass der User eine der erlaubten Rollen besitzt.
 */
export const requireRoles = (allowedRoles: string[]) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized: User not identified' });
      return;
    }

    if (!allowedRoles.includes(req.user.role)) {
      res.status(403).json({ 
        error: 'Forbidden: Insufficient role permissions',
        requiredRoles: allowedRoles 
      });
      return;
    }

    next();
  };
};

export const ROLES = {
  GLOBAL_ADMIN: 'GlobalAdmin',
  CENTRAL_HR: 'CentralHRCareerAdmin',
  LOCAL_EDITOR: 'LocalEditor',
  LOCAL_REVIEWER: 'LocalHiringReviewer',
  PUBLISHER: 'Publisher'
};
