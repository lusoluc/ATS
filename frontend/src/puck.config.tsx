import { Config } from '@measured/puck';
import React from 'react';
import { HomeHero, HomeStatBar, HomeTargetGroups, HomeBenefits, HomeEmployerBranding, HomeFAQ, HomeJobsTeaser } from './puck.home-components';

// Props Types für unsere Komponenten
export type Props = {
  HeroBlock: { title: string; subtitle: string; bgImage?: string; alignment: 'left' | 'center' | 'right'; titleSize: 'medium' | 'large' | 'xlarge'; textColor: 'white' | 'dark' };
  TextBlock: { content: string; leichteSpracheContent?: string; size: 'small' | 'default' | 'large' | 'xlarge'; color: 'default' | 'primary' | 'secondary' | 'muted'; align: 'left' | 'center' | 'right' };
  CallToAction: { buttonText: string; url: string; variant: 'primary' | 'secondary' };
  Spacer: { size: 'small' | 'medium' | 'large' };
  JobGrid: { title: string; limit: number };
  ImageBlock: { url: string; alt: string; caption?: string };
  QuoteBlock: { quote: string; author: string };
  Accordion: { items: { title: string; content: string }[] };
  HeaderNav: { logoText: string; links: { label: string; url: string }[] };
  FooterNav: { copyright: string; columns: { title: string; links: { label: string; url: string }[] }[] };
  FacilityInfo: { facilityName: string; address: string; showAddress: boolean; image?: string; description?: string };
  ContactCard: { name: string; role: string; email: string; phone?: string; showPhone: boolean; avatarUrl?: string };
  JobCard: { jobTitle: string; location: string; jobType: string; url: string; showApplyButton: boolean };
};

export const config: Config<any> = {
  components: {
    HeroBlock: {
      fields: {
        title: { type: 'text' },
        subtitle: { type: 'text' },
        bgImage: { type: 'text' },
        alignment: {
          type: 'radio',
          options: [
            { label: 'Links', value: 'left' },
            { label: 'Zentriert', value: 'center' },
            { label: 'Rechts', value: 'right' }
          ]
        },
        titleSize: {
          type: 'radio',
          options: [
            { label: 'Mittel', value: 'medium' },
            { label: 'Groß', value: 'large' },
            { label: 'Sehr Groß', value: 'xlarge' }
          ]
        },
        textColor: {
          type: 'radio',
          options: [
            { label: 'Weiß', value: 'white' },
            { label: 'Dunkel', value: 'dark' }
          ]
        }
      },
      defaultProps: {
        title: 'Willkommen',
        subtitle: 'Ihre Karriere beginnt hier',
        alignment: 'center',
        titleSize: 'large',
        textColor: 'white'
      },
      render: ({ title, subtitle, bgImage, alignment, titleSize, textColor }) => {
        const h1Size = titleSize === 'medium' ? '2.5rem' : titleSize === 'large' ? '3.5rem' : '4.5rem';
        const color = textColor === 'white' ? '#ffffff' : '#111827';
        return (
        <div style={{
          padding: '6rem 2rem',
          textAlign: alignment,
          background: bgImage ? `url(${bgImage}) center/cover` : 'var(--primary)',
          color: color,
          borderRadius: '16px',
          marginBottom: '2rem'
        }}>
          <h1 style={{ fontSize: h1Size, marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>{title}</h1>
          <p style={{ fontSize: '1.25rem', opacity: 0.9 }}>{subtitle}</p>
        </div>
      )}
    },
    TextBlock: {
      fields: {
        content: { type: 'textarea' },
        leichteSpracheContent: { type: 'textarea', label: 'Leichte Sprache (Optional)' },
        size: {
          type: 'radio',
          options: [
            { label: 'Klein', value: 'small' },
            { label: 'Standard', value: 'default' },
            { label: 'Groß', value: 'large' },
            { label: 'Sehr Groß', value: 'xlarge' }
          ]
        },
        color: {
          type: 'radio',
          options: [
            { label: 'Standard', value: 'default' },
            { label: 'Primärfarbe', value: 'primary' },
            { label: 'Sekundär', value: 'secondary' },
            { label: 'Dezent', value: 'muted' }
          ]
        },
        align: {
          type: 'radio',
          options: [
            { label: 'Links', value: 'left' },
            { label: 'Zentriert', value: 'center' },
            { label: 'Rechts', value: 'right' }
          ]
        }
      },
      defaultProps: {
        content: 'Fügen Sie hier Ihren Text ein. HTML wie <strong>Fett</strong> oder <em>Kursiv</em> ist möglich.',
        size: 'default',
        color: 'default',
        align: 'left'
      },
      render: ({ content, leichteSpracheContent, size, color, align }) => {
        const fontSize = size === 'small' ? '0.9rem' : size === 'large' ? '1.25rem' : size === 'xlarge' ? '1.5rem' : '1.1rem';
        const textColor = color === 'primary' ? 'var(--primary)' : color === 'secondary' ? 'var(--secondary)' : color === 'muted' ? '#6b7280' : '#374151';
        return (
        <div style={{ padding: '2rem 0', maxWidth: '800px', margin: '0 auto', fontSize: fontSize, color: textColor, textAlign: align, lineHeight: 1.8 }}>
          <div dangerouslySetInnerHTML={{ __html: content }} />
        </div>
      )}
    },
    CallToAction: {
      fields: {
        buttonText: { type: 'text' },
        url: { type: 'text' },
        variant: {
          type: 'radio',
          options: [
            { label: 'Hauptaktion (Primär)', value: 'primary' },
            { label: 'Nebenaktion (Sekundär)', value: 'secondary' }
          ]
        }
      },
      defaultProps: {
        buttonText: 'Jetzt bewerben',
        url: '/bewerben',
        variant: 'primary'
      },
      render: ({ buttonText, url, variant }) => (
        <div style={{ padding: '2rem 0', textAlign: 'center' }}>
          <a href={url} style={{
            display: 'inline-block',
            padding: '1rem 2.5rem',
            background: variant === 'primary' ? 'var(--secondary)' : 'transparent',
            color: variant === 'primary' ? 'white' : 'var(--secondary)',
            border: variant === 'secondary' ? '2px solid var(--secondary)' : 'none',
            borderRadius: '999px',
            textDecoration: 'none',
            fontWeight: 'bold',
            fontSize: '1.1rem'
          }}>
            {buttonText}
          </a>
        </div>
      )
    },
    Spacer: {
      fields: {
        size: {
          type: 'radio',
          options: [
            { label: 'Klein', value: 'small' },
            { label: 'Mittel', value: 'medium' },
            { label: 'Groß', value: 'large' }
          ]
        }
      },
      defaultProps: { size: 'medium' },
      render: ({ size }) => {
        const height = size === 'small' ? '2rem' : size === 'medium' ? '4rem' : '8rem';
        return <div style={{ height, width: '100%' }} />;
      }
    },
    JobGrid: {
      fields: {
        title: { type: 'text' },
        limit: { type: 'number' }
      },
      defaultProps: {
        title: 'Aktuelle Stellenangebote',
        limit: 3
      },
      render: ({ title, limit }) => (
        <div style={{ padding: '4rem 0' }}>
          <h2 style={{ fontSize: '2rem', marginBottom: '2rem', textAlign: 'center' }}>{title}</h2>
          <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {/* Platzhalter-Karten, die in Produktion durch echte DB-Daten gefüllt werden */}
            {Array.from({ length: limit }).map((_, i) => (
              <div key={i} style={{ padding: '1.5rem', border: '1px solid #e5e7eb', borderRadius: '12px', width: '300px' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Pflegefachkraft (m/w/d)</div>
                <div style={{ opacity: 0.7, marginBottom: '1rem' }}>Standort {i + 1}</div>
                <a href="/jobs" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>Details ansehen</a>
              </div>
            ))}
          </div>
        </div>
      )
    },
    ImageBlock: {
      fields: {
        url: { type: 'text' },
        alt: { type: 'text' },
        caption: { type: 'text' }
      },
      defaultProps: { url: 'https://via.placeholder.com/800x400', alt: 'Bildbeschreibung' },
      render: ({ url, alt, caption }) => (
        <figure style={{ margin: '2rem auto', maxWidth: '800px', textAlign: 'center' }}>
          <img src={url} alt={alt} style={{ maxWidth: '100%', borderRadius: '12px', boxShadow: 'var(--shadow)' }} />
          {caption && <figcaption style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#6b7280' }}>{caption}</figcaption>}
        </figure>
      )
    },
    QuoteBlock: {
      fields: {
        quote: { type: 'textarea' },
        author: { type: 'text' }
      },
      defaultProps: { quote: 'Das ist ein fantastisches Zitat.', author: 'Max Mustermann' },
      render: ({ quote, author }) => (
        <blockquote style={{ margin: '3rem auto', maxWidth: '600px', padding: '2rem', background: '#f3f4f6', borderRadius: '16px', borderLeft: '6px solid var(--secondary)' }}>
          <p style={{ fontSize: '1.4rem', fontStyle: 'italic', marginBottom: '1rem' }}>"{quote}"</p>
          <footer style={{ fontWeight: 'bold' }}>— {author}</footer>
        </blockquote>
      )
    },
    Accordion: {
      fields: {
        items: {
          type: 'array',
          arrayFields: {
            title: { type: 'text' },
            content: { type: 'textarea' }
          }
        }
      },
      defaultProps: {
        items: [{ title: 'Frage 1', content: 'Antwort 1' }]
      },
      render: ({ items }) => (
        <div style={{ maxWidth: '800px', margin: '2rem auto' }}>
          {items.map((item, i) => (
            <details key={i} style={{ marginBottom: '1rem', padding: '1rem', background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
              <summary style={{ fontWeight: 'bold', cursor: 'pointer', fontSize: '1.1rem' }}>{item.title}</summary>
              <p style={{ marginTop: '1rem', color: '#4b5563', lineHeight: 1.6 }}>{item.content}</p>
            </details>
          ))}
        </div>
      )
    },
    HeaderNav: {
      fields: {
        logoText: { type: 'text' },
        links: {
          type: 'array',
          arrayFields: { label: { type: 'text' }, url: { type: 'text' } }
        }
      },
      defaultProps: {
        logoText: 'Enterprise',
        links: [{ label: 'Stellenangebote', url: '/jobs' }, { label: 'Arbeitgeber', url: '/arbeitgeber' }]
      },
      render: ({ logoText, links }) => (
        <nav style={{ padding: '1rem 2rem', background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(10px)', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="/" style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--primary)', textDecoration: 'none' }}>{logoText}</a>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            {links.map((l, i) => <a key={i} href={l.url} style={{ color: 'var(--foreground)', textDecoration: 'none', fontWeight: 'bold' }}>{l.label}</a>)}
          </div>
        </nav>
      )
    },
    FooterNav: {
      fields: {
        copyright: { type: 'text' },
        columns: {
          type: 'array',
          arrayFields: {
            title: { type: 'text' },
            links: { type: 'array', arrayFields: { label: { type: 'text' }, url: { type: 'text' } } }
          }
        }
      },
      defaultProps: {
        copyright: '© 2026 Enterprise Karriere',
        columns: [
          { title: 'Rechtliches', links: [{ label: 'Impressum', url: '/info/impressum' }] }
        ]
      },
      render: ({ copyright, columns }) => (
        <footer style={{ background: '#1f2937', color: 'white', padding: '4rem 2rem 2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', maxWidth: '1200px', margin: '0 auto', paddingBottom: '2rem', borderBottom: '1px solid #374151' }}>
            {columns.map((col, i) => (
              <div key={i}>
                <h4 style={{ color: 'var(--primary)', marginBottom: '1rem', fontSize: '1.2rem' }}>{col.title}</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {col.links.map((l, j) => <a key={j} href={l.url} style={{ color: '#d1d5db', textDecoration: 'none' }}>{l.label}</a>)}
                </div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', paddingTop: '2rem', color: '#9ca3af', fontSize: '0.9rem' }}>{copyright}</div>
        </footer>
      )
    },
    FacilityInfo: {
      fields: {
        facilityName: { type: 'text' },
        description: { type: 'textarea' },
        address: { type: 'text' },
        showAddress: {
          type: 'radio',
          options: [{ label: 'Ja', value: 'true' }, { label: 'Nein', value: 'false' }]
        },
        image: { type: 'text' }
      },
      defaultProps: {
        facilityName: 'Klinik am Park',
        description: 'Eine moderne Einrichtung im Herzen der Natur.',
        address: 'Musterstraße 1, 12345 Musterstadt',
        showAddress: 'true' as any, // Puck radios handle strings
        image: 'https://via.placeholder.com/600x400'
      },
      render: ({ facilityName, description, address, showAddress, image }) => (
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'center', background: 'var(--surface)', padding: '2rem', borderRadius: '16px', boxShadow: 'var(--shadow)', margin: '2rem auto', maxWidth: '900px' }}>
          {image && <img src={image} alt={facilityName} style={{ flex: '1 1 300px', maxWidth: '400px', borderRadius: '12px', objectFit: 'cover' }} />}
          <div style={{ flex: '2 1 300px' }}>
            <h3 style={{ fontSize: '1.8rem', color: 'var(--primary)', marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>{facilityName}</h3>
            {description && <p style={{ fontSize: '1rem', lineHeight: 1.6, opacity: 0.8, marginBottom: '1rem' }}>{description}</p>}
            {String(showAddress) === 'true' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: 0.7, fontSize: '0.9rem' }}>
                📍 {address}
              </div>
            )}
          </div>
        </div>
      )
    },
    ContactCard: {
      fields: {
        name: { type: 'text' },
        role: { type: 'text' },
        email: { type: 'text' },
        phone: { type: 'text' },
        showPhone: {
          type: 'radio',
          options: [{ label: 'Ja', value: 'true' }, { label: 'Nein', value: 'false' }]
        },
        avatarUrl: { type: 'text' }
      },
      defaultProps: {
        name: 'Dr. Maria Muster',
        role: 'Chefärztin',
        email: 'bewerbung@Enterprise.de',
        phone: '+49 123 456789',
        showPhone: 'true' as any,
        avatarUrl: 'https://via.placeholder.com/150'
      },
      render: ({ name, role, email, phone, showPhone, avatarUrl }) => (
        <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border)', maxWidth: '350px', margin: '2rem auto', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {avatarUrl && <img src={avatarUrl} alt={name} style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--secondary)' }} />}
          <div>
            <strong style={{ display: 'block', fontSize: '1.2rem', color: 'var(--foreground)' }}>{name}</strong>
            <span style={{ fontSize: '0.9rem', color: 'var(--primary)', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>{role}</span>
            <a href={`mailto:${email}`} style={{ display: 'block', fontSize: '0.85rem', color: '#6b7280', textDecoration: 'none' }}>✉️ E-Mail schreiben</a>
            {String(showPhone) === 'true' && phone && (
              <a href={`tel:${phone.replace(/\s+/g, '')}`} style={{ display: 'block', fontSize: '0.85rem', color: '#6b7280', textDecoration: 'none', marginTop: '0.2rem' }}>📞 {phone}</a>
            )}
          </div>
        </div>
      )
    },
    JobCard: {
      fields: {
        jobTitle: { type: 'text' },
        location: { type: 'text' },
        jobType: { type: 'text' },
        url: { type: 'text' },
        showApplyButton: {
          type: 'radio',
          options: [{ label: 'Ja', value: 'true' }, { label: 'Nein', value: 'false' }]
        }
      },
      defaultProps: {
        jobTitle: 'Pflegefachkraft (m/w/d)',
        location: 'Klinik am Park',
        jobType: 'Vollzeit',
        url: '/jobs/123',
        showApplyButton: 'true' as any
      },
      render: ({ jobTitle, location, jobType, url, showApplyButton }) => (
        <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e5e7eb', maxWidth: '600px', margin: '1rem auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', boxShadow: 'var(--shadow)' }}>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase' }}>{jobType}</span>
            <h4 style={{ margin: '0.2rem 0', fontSize: '1.2rem', color: 'var(--foreground)' }}>{jobTitle}</h4>
            <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>📍 {location}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <a href={url} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--foreground)', textDecoration: 'none' }}>Details</a>
            {String(showApplyButton) === 'true' && (
              <a href={`/bewerben?jobId=123`} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', background: 'var(--primary)', color: 'white', borderRadius: '6px', textDecoration: 'none', fontWeight: 'bold' }}>Bewerben</a>
            )}
          </div>
        </div>
      )
    },
    HomeHero,
    HomeStatBar,
    HomeTargetGroups,
    HomeBenefits,
    HomeEmployerBranding,
    HomeFAQ,
    HomeJobsTeaser
  }
};
