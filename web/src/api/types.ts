export interface Horse {
  id: number
  name: string
  description: string | null
  reference_image_path: string
  created_at: string
}

export interface HorseDetail {
  horse: Horse
  recent_detections: Detection[]
}

export interface Location {
  id: number
  name: string
  description: string | null
}

export interface HorseScore {
  horse_id: number | null
  horse_name: string
  probability: number
}

export interface Detection {
  id: number
  horse_id: number | null
  location_id: number
  image_path: string
  timestamp: string
  action: string
  confidence: number
  raw_vlm_response: string | null
  created_at: string
  horse_scores: HorseScore[] | null
}

export interface AnalyzeResponse {
  detection_id: number
  horse_id: number | null
  horse_name: string | null
  location_id: number
  action: string
  confidence: number
  kept: boolean
  timestamp: string
  image_path: string
  raw_vlm_response: string | null
  horse_scores: HorseScore[]
}
