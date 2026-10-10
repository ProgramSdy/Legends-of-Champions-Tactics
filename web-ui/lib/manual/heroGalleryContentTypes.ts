export interface HeroGalleryStrategyTip {
  label: string;
  text: string;
}

export interface HeroGallerySkillContent {
  introduction: string;
  tips?: readonly HeroGalleryStrategyTip[];
}

export interface HeroGalleryHeroContent {
  introduction: string;
  battleStyle: string;
  skills: Readonly<Record<string, HeroGallerySkillContent>>;
}

export type HeroGalleryContentRegistry = Readonly<Record<string, HeroGalleryHeroContent>>;
