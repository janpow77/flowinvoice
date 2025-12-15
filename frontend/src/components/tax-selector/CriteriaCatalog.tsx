/**
 * CriteriaCatalog Component
 *
 * Modal mit vollständigem Kriterienkatalog eines Steuersystems.
 */

import { useTranslation } from 'react-i18next';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import clsx from 'clsx';
import { Button } from '@/components/ui';
import { getRuleset, type RulesetId, type RulesetFeature } from '@/lib/rulesets';

interface CriteriaCatalogProps {
  rulesetId: RulesetId;
  onClose: () => void;
  onConfirm: () => void;
}

const categoryIcons: Record<string, string> = {
  IDENTITY: '🆔',
  DATE: '📅',
  AMOUNT: '💰',
  TAX: '📊',
  TEXT: '📝',
  SEMANTIC: '🤖',
  PROJECT: '📁',
};

const categoryNames: Record<string, { de: string; en: string }> = {
  IDENTITY: { de: 'Identifikation', en: 'Identification' },
  DATE: { de: 'Datumsangaben', en: 'Date Information' },
  AMOUNT: { de: 'Beträge', en: 'Amounts' },
  TAX: { de: 'Steuerangaben', en: 'Tax Information' },
  TEXT: { de: 'Textfelder', en: 'Text Fields' },
  SEMANTIC: { de: 'Semantik', en: 'Semantic' },
  PROJECT: { de: 'Projektbezug', en: 'Project Context' },
};

function FeatureItem({
  feature,
  lang,
}: {
  feature: RulesetFeature;
  lang: 'de' | 'en';
}) {
  const isRequired = feature.required_level === 'REQUIRED';
  const isConditional = feature.required_level === 'CONDITIONAL';

  return (
    <div
      className={clsx(
        'flex items-start gap-3 p-3 rounded-lg',
        isRequired ? 'bg-gray-50' : 'bg-yellow-50'
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        {isRequired ? (
          <CheckCircle className="w-5 h-5 text-success-500" />
        ) : (
          <AlertCircle className="w-5 h-5 text-warning-500" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm">{categoryIcons[feature.category]}</span>
          <span className="font-medium text-gray-900">
            {lang === 'de' ? feature.name_de : feature.name_en}
          </span>
          {isConditional && (
            <span className="px-2 py-0.5 text-xs bg-warning-100 text-warning-700 rounded">
              {lang === 'de' ? 'Bedingt' : 'Conditional'}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-1">
          {lang === 'de' ? feature.explanation_de : feature.explanation_en}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {feature.legal_basis}
        </p>
      </div>
    </div>
  );
}

export function CriteriaCatalog({
  rulesetId,
  onClose,
  onConfirm,
}: CriteriaCatalogProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language as 'de' | 'en';
  const ruleset = getRuleset(rulesetId);

  // Features nach Kategorie gruppieren
  const groupedFeatures = ruleset.features.reduce((acc, feature) => {
    const cat = feature.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(feature);
    return acc;
  }, {} as Record<string, RulesetFeature[]>);

  const requiredCount = ruleset.features.filter(
    (f) => f.required_level === 'REQUIRED'
  ).length;
  const conditionalCount = ruleset.features.filter(
    (f) => f.required_level === 'CONDITIONAL'
  ).length;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{ruleset.flag}</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  {lang === 'de' ? ruleset.title_de : ruleset.title_en}
                </h2>
                <p className="text-sm text-gray-500">
                  {lang === 'de' ? ruleset.subtitle_de : ruleset.subtitle_en}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label={t('common.close')}
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-180px)]">
            {/* Statistik */}
            <div className="flex gap-4 mb-6">
              <div className="flex-1 bg-success-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-success-700">
                  {requiredCount}
                </div>
                <div className="text-sm text-success-600">
                  {lang === 'de' ? 'Pflichtangaben' : 'Required fields'}
                </div>
              </div>
              <div className="flex-1 bg-warning-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-warning-700">
                  {conditionalCount}
                </div>
                <div className="text-sm text-warning-600">
                  {lang === 'de' ? 'Bedingte Angaben' : 'Conditional fields'}
                </div>
              </div>
              {ruleset.small_amount_threshold && (
                <div className="flex-1 bg-info-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-info-700">
                    ≤ {ruleset.small_amount_threshold} {ruleset.small_amount_currency}
                  </div>
                  <div className="text-sm text-info-600">
                    {lang === 'de' ? 'Kleinbetragsgrenze' : 'Small amount limit'}
                  </div>
                </div>
              )}
            </div>

            {/* Rechtsgrundlagen */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Info className="w-4 h-4" />
                {lang === 'de' ? 'Rechtsgrundlagen' : 'Legal References'}
              </h3>
              <ul className="text-sm text-gray-600 space-y-1">
                {ruleset.legal_references.map((ref, idx) => (
                  <li key={idx}>
                    <span className="font-medium">{ref.law} {ref.section}</span>
                    {' – '}
                    {lang === 'de' ? ref.description_de : ref.description_en}
                  </li>
                ))}
              </ul>
            </div>

            {/* Features nach Kategorie */}
            {Object.entries(groupedFeatures).map(([category, features]) => (
              <div key={category} className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <span>{categoryIcons[category]}</span>
                  {lang === 'de'
                    ? categoryNames[category]?.de
                    : categoryNames[category]?.en}
                  <span className="text-sm font-normal text-gray-400">
                    ({features.length})
                  </span>
                </h3>
                <div className="space-y-2">
                  {features.map((feature) => (
                    <FeatureItem
                      key={feature.feature_id}
                      feature={feature}
                      lang={lang}
                    />
                  ))}
                </div>
              </div>
            ))}

            {/* Kleinbetragshinweis */}
            {ruleset.small_amount_threshold && (
              <div className="p-4 bg-info-50 border border-info-200 rounded-lg">
                <h4 className="font-semibold text-info-800 mb-1">
                  {lang === 'de'
                    ? `Kleinbetragsrechnung (≤ ${ruleset.small_amount_threshold} ${ruleset.small_amount_currency})`
                    : `Small Amount Invoice (≤ ${ruleset.small_amount_threshold} ${ruleset.small_amount_currency})`}
                </h4>
                <p className="text-sm text-info-700">
                  {lang === 'de'
                    ? 'Bei Rechnungen bis zu diesem Betrag gelten reduzierte Anforderungen. Nur Merkmale mit dem Attribut "Kleinbetragsrechnung" sind dann erforderlich.'
                    : 'Invoices up to this amount have reduced requirements. Only fields marked as applicable to small amount invoices are required.'}
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
            <Button variant="ghost" onClick={onClose}>
              {t('common.cancel', 'Abbrechen')}
            </Button>
            <Button variant="primary" onClick={onConfirm}>
              {ruleset.flag} {t('taxSelector.confirm', 'Auswahl bestätigen')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CriteriaCatalog;
