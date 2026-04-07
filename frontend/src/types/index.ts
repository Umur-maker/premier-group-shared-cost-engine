export interface Company {
  id: string;
  name: string;
  area_m2: number;
  headcount_default: number;
  building: string;
  floor: string;
  office_no: string;
  has_heating: boolean;
  electricity_eligible: boolean;
  water_eligible: boolean;
  garbage_eligible: boolean;
  active: boolean;
  contact_person: string;
  phone: string;
  email: string;
  beginning_date: string;
  expiration_date: string;
  notes: string;
  monthly_rent_eur: number;
  maintenance_rate_eur: number;
}

export interface RatioWeight {
  sqm_weight: number;
  headcount_weight: number;
}

export interface Settings {
  ratios: Record<string, RatioWeight>;
  eur_ron_rate: number;
  cost_categories: Record<string, CostCategory>;
}

export interface CostCategory {
  amount_type: string;
  allocation?: string;
  ratio_key?: string;
  eligible: string;
  include_companies?: string[];
  exclude_companies?: string[];
  exclude_floors?: string[];
  rate_eur?: number;
  amount_eur?: number;
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
  consumables_total: number;
  printer_total: number;
  internet_total: number;
  cleaning_cost: number;
  security_cameras_cost: number;
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
  consumables: number;
  printer: number;
  internet: number;
  maintenance: number;
  rent: number;
  total: number;
}

export interface CalculateResponse {
  results: AllocationResult[];
  filename: string;
}

export interface SaveResponse {
  run_id: string;
  filename: string;
  replaced: string | null;
  results: AllocationResult[];
}

export interface MonthCheck {
  exists: boolean;
  run_id?: string;
  generated_at?: string;
}

export interface HistoryEntry {
  id: string;
  month: number;
  year: number;
  language: string;
  generated_at: string;
  excel_file: string;
  monthly_input: MonthlyInput;
  ratios: Record<string, RatioWeight>;
  company_count: number;
}

export interface PaymentEntry {
  id: string;
  run_id: string;
  company_id: string;
  amount: number;
  date: string;
  note: string;
  created_at: string;
}
