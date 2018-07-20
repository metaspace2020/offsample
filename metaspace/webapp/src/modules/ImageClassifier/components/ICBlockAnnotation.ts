
export interface MzImage {
  mz: number;
  url: string;
  totalIntensity: number;
  minIntensity: number;
  maxIntensity: number;
}

export interface ICBlockAnnotation {
  id: string;
  sumFormula: string;
  adduct: string;
  msmScore: number;
  fdrLevel: number;
  mz: number;
  isotopeImages: MzImage[];
}
