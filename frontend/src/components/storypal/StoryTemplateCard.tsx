/**
 * Story Template Card
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Displays a story template as a selectable card with category, characters, and description.
 */

import { BookOpen, Users } from 'lucide-react'
import type { StoryTemplate } from '@/types/storypal'
import { STORY_CATEGORIES } from '@/types/storypal'
import { cn } from '@/lib/utils'

interface StoryTemplateCardProps {
  template: StoryTemplate
  isSelected: boolean
  onSelect: (template: StoryTemplate) => void
}

export function StoryTemplateCard({ template, isSelected, onSelect }: StoryTemplateCardProps) {
  const category = STORY_CATEGORIES[template.category]

  return (
    <button
      onClick={() => onSelect(template)}
      className={cn(
        'w-full rounded-lg border p-4 text-left transition-all hover:shadow-md',
        isSelected
          ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
          : 'border-border bg-card hover:border-primary/50'
      )}
    >
      {/* Category badge */}
      <div className="mb-2 flex items-center gap-2">
        <span className="text-lg">{category?.emoji}</span>
        <span className={cn('text-xs font-medium', category?.color)}>
          {category?.label}
        </span>
        <span className="ml-auto text-xs text-muted-foreground">
          {template.target_age_min}-{template.target_age_max} 歲
        </span>
      </div>

      {/* Title */}
      <h3 className="mb-1 text-sm font-semibold">{template.name}</h3>

      {/* Description */}
      <p className="mb-3 line-clamp-2 text-xs text-muted-foreground">
        {template.description}
      </p>

      {/* Characters preview */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <Users className="h-3 w-3" />
          {template.characters.length} 個角色
        </span>
        <span className="flex items-center gap-1">
          <BookOpen className="h-3 w-3" />
          {template.scenes.length} 個場景
        </span>
      </div>

      {/* Character names */}
      <div className="mt-2 flex flex-wrap gap-1">
        {template.characters.slice(0, 4).map((char) => (
          <span
            key={char.name}
            className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            {char.name}
          </span>
        ))}
        {template.characters.length > 4 && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
            +{template.characters.length - 4}
          </span>
        )}
      </div>
    </button>
  )
}
