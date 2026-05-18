import crypto from 'crypto';

// In einer echten Umgebung aus proccess.env.STORAGE_ENCRYPTION_KEY laden
// Falls nicht gesetzt, generieren wir für Entwicklungszwecke einen deterministischen Dummy-Key.
const ENCRYPTION_KEY = process.env.STORAGE_ENCRYPTION_KEY 
  ? Buffer.from(process.env.STORAGE_ENCRYPTION_KEY, 'hex') 
  : crypto.scryptSync('dummy-secret-key', 'salt', 32); 

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;

/**
 * Verschlüsselt einen Buffer (z.B. eine PDF-Datei) mit AES-256-GCM.
 * Gibt einen neuen Buffer zurück, der den IV (16 Bytes), den Auth-Tag (16 Bytes) und den Ciphertext enthält.
 */
export function encryptBuffer(buffer: Buffer): Buffer {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, ENCRYPTION_KEY, iv);
  
  const encrypted = Buffer.concat([cipher.update(buffer), cipher.final()]);
  const authTag = cipher.getAuthTag(); // 16 bytes

  // Resultat-Format: IV (16) + AuthTag (16) + Encrypted Data
  return Buffer.concat([iv, authTag, encrypted]);
}

/**
 * Entschlüsselt einen AES-256-GCM verschlüsselten Buffer.
 * Liest den IV und den Auth-Tag aus und entschlüsselt die eigentlichen Daten.
 */
export function decryptBuffer(encryptedBuffer: Buffer): Buffer {
  if (encryptedBuffer.length < IV_LENGTH + 16) {
    throw new Error('Buffer zu klein. Keine gültige verschlüsselte Datei.');
  }

  const iv = encryptedBuffer.subarray(0, IV_LENGTH);
  const authTag = encryptedBuffer.subarray(IV_LENGTH, IV_LENGTH + 16);
  const data = encryptedBuffer.subarray(IV_LENGTH + 16);

  const decipher = crypto.createDecipheriv(ALGORITHM, ENCRYPTION_KEY, iv);
  decipher.setAuthTag(authTag);

  const decrypted = Buffer.concat([decipher.update(data), decipher.final()]);
  return decrypted;
}
