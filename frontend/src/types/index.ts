export interface Company {
  id: string;
  name: string;
  area_m2: number;
  headcount_default: number;
  building: string;
  floor: string;
  has_heating: boolean;
  electricity_eligible: boolean;
  water_eligible: boolean;
  garbage_eligible: boolean;
  active: boolean;
  office_location: string;
  contact_person: string;
  phone: string;
  email: string;
  beginning_date: string;
  expiration_date: string;
  notes: string;
}

export interface RatioWeight {
  sqm_weight: number;
  headcount_weight: number;
}

export interface Settings {
  ratios: {
    electricity: RatioWeight;
    gas: RatioWeight;
    water: RatioWeight;
    garbage: RatioWeight;
  };
}

export interface MonthlyInput {
  electricity_total: number;
  water_total: number;
  garbage_total: number;
  hotel_gas_total: number;
  ground_floor_gas_total: number;
  first_floor_gas_total: number;
  external_electricity: number;
  external_water: number;
  external_garbage: number;
  external_hotel_gas: number;
  external_gf_gas: number;
  external_ff_gas: number;
}

export interface AllocationResult {
  company_id: string;
  company_name: string;
  electricity: number;
  water: number;
  garbage: number;
  gas_hotel: number;
  gas_ground_floor: number;
  gas_first_floor: number;
  total: number;
}

export interface CalculateResponse {
  results: AllocationResult[];
  filename: string;
  run_id: string;
}

export interface HistoryEntry {
  id: string;
  month: number;
  year: number;
  language: string;
  generated_at: string;
  excel_file: string;
  monthly_input: MonthlyInput;
  ratios: Settings["ratios"];
  company_count: number;
}
