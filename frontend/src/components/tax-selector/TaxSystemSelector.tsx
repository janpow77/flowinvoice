/**
 * TaxSystemSelector Component
 *
 * Hauptkomponente für die Steuersystem-Auswahl mit Flaggen.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TaxSystemCard } from './TaxSystemCard';
import { CriteriaCatalog } from './CriteriaCatalog';
import { getRulesetSummaries, type RulesetId } from '@/lib/rulesets';

interface TaxSystemSelectorProps {
  /** Aktuell ausgewähltes Ruleset */
  currentRuleset?: RulesetId;
  /** Callback wenn Ruleset ausgewählt wird */
  onSelect: (rulesetId: RulesetId) => void;
  /** Kompakte Darstellung */
  compact?: boolean;
}

export function TaxSystemSelector({
  currentRuleset,
  onSelect,
  compact = false,
}: TaxSystemSelectorProps) {
  const { t, i18n } = useTranslation();
  const [showCatalog, setShowCatalog] = useState<RulesetId | null>(null);
  const lang = i18n.language as 'de' | 'en';

  const rulesets = getRulesetSummaries();

  const handleCardClick = (rulesetId: RulesetId) => {
    setShowCatalog(rulesetId);
  };

  const handleConfirm = () => {
    if (showCatalog) {
      onSelect(showCatalog);
      setShowCatalog(null);
    }
  };

  return (
    <div>
      {/* Header */}
      {!compact && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {t('taxSelector.title', 'Steuersystem auswählen')}
          </h3>
          <p className="text-sm text-gray-500">
            {t('taxSelector.description', 'Wählen Sie das Steuersystem für die Rechnungsprüfung')}
          </p>
        </div>
      )}

      {/* Flaggen-Karten */}
      <div
        className={`grid gap-4 ${
          compact ? 'grid-cols-3' : 'grid-cols-1 sm:grid-cols-3'
        }`}
      >
        {rulesets.map((rs) => (
          <TaxSystemCard
            key={rs.ruleset_id}
            flag={rs.flag}
            title={lang === 'de' ? rs.title_de : rs.title_en}
            subtitle={lang === 'de' ? rs.subtitle_de : rs.subtitle_en}
            featureCount={rs.feature_count}
            isSelected={currentRuleset === rs.ruleset_id}
            onClick={() => handleCardClick(rs.ruleset_id)}
          />
        ))}
      </div>

      {/* Hinweis */}
      {!compact && (
        <p className="mt-4 text-xs text-gray-400 text-center">
          {t(
            'taxSelector.hint',
            'Die Sprachwahl (DE/EN) der Benutzeroberfläche ist unabhängig vom Steuersystem'
          )}
        </p>
      )}

      {/* Kriterienkatalog Modal */}
      {showCatalog && (
        <CriteriaCatalog
          rulesetId={showCatalog}
          onClose={() => setShowCatalog(null)}
          onConfirm={handleConfirm}
        />
      )}
    </div>
  );
}

export default TaxSystemSelector;
