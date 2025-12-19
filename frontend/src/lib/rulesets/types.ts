/**
 * Ruleset Type Definitions
 *
 * Typen für Steuersysteme und ihre Pflichtmerkmale.
 */

export type RulesetId = 'DE_USTG' | 'EU_VAT' | 'UK_VAT';

export type DocumentType = 'INVOICE' | 'BANK_STATEMENT' | 'PROCUREMENT' | 'CONTRACT' | 'OTHER';

export type RequiredLevel = 'REQUIRED' | 'CONDITIONAL' | 'OPTIONAL';

export type FeatureCategory =
  | 'IDENTITY'      // Identifikation (Namen, Adressen, IDs)
  | 'DATE'          // Datums-/Zeitangaben
  | 'AMOUNT'        // Geldbeträge
  | 'TAX'           // Steuerliche Angaben
  | 'TEXT'          // Textfelder
  | 'SEMANTIC'      // Semantische Prüfungen (KI)
  | 'PROJECT';      // Projektbezogene Prüfungen

export interface LegalReference {
  law: string;
  section: string;
  description_de: string;
  description_en: string;
}

export interface RulesetFeature {
  feature_id: string;
  name_de: string;
  name_en: string;
  legal_basis: string;
  required_level: RequiredLevel;
  category: FeatureCategory;
  explanation_de: string;
  explanation_en: string;
  validation?: {
    regex?: string;
    min_length?: number;
    max_length?: number;
  };
  applies_to?: {
    standard_invoice: boolean;
    small_amount_invoice: boolean;
  };
}

export interface Ruleset {
  ruleset_id: RulesetId;
  version: string;
  jurisdiction: string;
  flag: string;
  title_de: string;
  title_en: string;
  subtitle_de: string;
  subtitle_en: string;
  legal_references: LegalReference[];
  features: RulesetFeature[];
  supported_document_types?: DocumentType[];
  small_amount_threshold?: number;
  small_amount_currency?: string;
  vat_rates?: number[];
}

export interface RulesetSummary {
  ruleset_id: RulesetId;
  flag: string;
  title_de: string;
  title_en: string;
  subtitle_de: string;
  subtitle_en: string;
  feature_count: number;
}
