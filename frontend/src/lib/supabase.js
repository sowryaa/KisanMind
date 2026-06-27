import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://ezliecbtqpehkxirdxit.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6bGllY2J0cXBlaGt4aXJkeGl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNTQwOTQsImV4cCI6MjA5NzkzMDA5NH0.8pJJi7fklahyrR3bY2_4i_m_yGKjFFO03Hz8XXNcEM8'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
