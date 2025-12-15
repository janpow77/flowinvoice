/**
 * Rulesets Export
 *
 * Zentrale Export-Datei für alle Steuersystem-Regelwerke.
 */

export * from './types';
export { DE_USTG } from './DE_USTG';
export { EU_VAT } from './EU_VAT';
export { UK_VAT } from './UK_VAT';

import type { Ruleset, RulesetId, RulesetSummary } from './types';
import { DE_USTG } from './DE_USTG';
import { EU_VAT } from './EU_VAT';
import { UK_VAT } from './UK_VAT';

/**
 * Alle verfügbaren Rulesets
 */
export const RULESETS: Record<RulesetId, Ruleset> = {
  DE_USTG,
  EU_VAT,
  UK_VAT,
};

/**
 * Ruleset nach ID laden
 */
export function getRuleset(id: RulesetId): Ruleset {
  const ruleset = RULESETS[id];
  if (!ruleset) {
    throw new Error(`Ruleset ${id} not found`);
  }
  return ruleset;
}

/**
 * Alle Rulesets als Array
 */
export function getAllRulesets(): Ruleset[] {
  return Object.values(RULESETS);
}

/**
 * Ruleset-Übersichten für Auswahl-UI
 */
export function getRulesetSummaries(): RulesetSummary[] {
  return getAllRulesets().map((rs) => ({
    ruleset_id: rs.ruleset_id,
    flag: rs.flag,
    title_de: rs.title_de,
    title_en: rs.title_en,
    subtitle_de: rs.subtitle_de,
    subtitle_en: rs.subtitle_en,
    feature_count: rs.features.filter((f) => f.required_level === 'REQUIRED').length,
  }));
}

/**
 * Pflichtmerkmale eines Rulesets filtern
 */
export function getRequiredFeatures(id: RulesetId, isSmallAmount: boolean = false) {
  const ruleset = getRuleset(id);
  return ruleset.features.filter((f) => {
    if (f.required_level !== 'REQUIRED') return false;
    if (isSmallAmount && f.applies_to) {
      return f.applies_to.small_amount_invoice;
    }
    return true;
  });
}

/**
 * Prüft ob Betrag unter Kleinbetragsgrenze liegt
 */
export function isSmallAmountInvoice(id: RulesetId, grossAmount: number): boolean {
  const ruleset = getRuleset(id);
  if (!ruleset.small_amount_threshold) return false;
  return grossAmount <= ruleset.small_amount_threshold;
}
