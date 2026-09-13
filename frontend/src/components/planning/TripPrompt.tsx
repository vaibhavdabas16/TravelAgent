import { useState } from 'react';
import { ArrowRight } from 'lucide-react';

interface TripPromptProps {
  onSubmit: (query: string) => void;
  initialValue?: string;
  autoFocus?: boolean;
}

const EXAMPLES = ['7 days in Japan with food and temples', 'Weekend in Lisbon', 'Family trip to Bali in August'];

/** The single most important input. Free text; structure comes after. */
export function TripPrompt({ onSubmit, initialValue = '', autoFocus = false }: TripPromptProps) {
  const [value, setValue] = useState(initialValue);
  const submit = (text: string) => {
    const t = text.trim();
    if (t) onSubmit(t);
  };

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(value);
        }}
        className="rounded-md border border-rule-2 bg-paper focus-within:border-ink focus-within:ring-1 focus-within:ring-ink"
      >
        <label htmlFor="trip-prompt" className="sr-only">
          Describe your trip
        </label>
        <textarea
          id="trip-prompt"
          value={value}
          autoFocus={autoFocus}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit(value);
            }
          }}
          rows={3}
          placeholder="e.g. 6 days in Kyoto in October, two of us, food and temples, hotels under ₹15,000 a night, flying from Delhi"
          className="block w-full resize-none bg-transparent px-3 pt-3 pb-1 text-[14px] leading-relaxed placeholder:text-subtle focus:outline-none"
        />
        <div className="flex items-center justify-between px-2 pb-2">
          <span className="mono px-1 text-subtle">Enter to plan</span>
          <button type="submit" disabled={!value.trim()} className="btn btn-primary">
            Plan trip
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </form>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-subtle">
        <span>Try</span>
        {EXAMPLES.map((e) => (
          <button key={e} type="button" onClick={() => submit(e)} className="text-muted underline-offset-2 hover:text-ink hover:underline">
            {e}
          </button>
        ))}
      </div>
    </div>
  );
}
