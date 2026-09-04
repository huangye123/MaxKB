import { Result } from '@/request/Result'
import { get, post, put } from '@/request/index'
import { type Ref } from 'vue'

const prefix = '/platform'

export interface PlatformSourceConfig {
  [key: string]: string
}

export interface PlatformSource {
  id?: string
  auth_type: string
  config: PlatformSourceConfig
  type?: string
  is_active: boolean
  is_valid: boolean
}

const normalizePlatformSourceResult = (
  result: Result<PlatformSource[] | null | undefined>,
): Result<PlatformSource[]> => {
  return {
    ...result,
    data: Array.isArray(result.data) ? result.data : [],
  }
}

const getPlatformInfo: (loading?: Ref<boolean>) => Promise<Result<PlatformSource[]>> = (
  loading,
) => {
  return get(`${prefix}/source`, undefined, loading).then(normalizePlatformSourceResult)
}

const updateConfig: (data: any, loading?: Ref<boolean>) => Promise<Result<any>> = (
  data,
  loading,
) => {
  return post(`${prefix}/source`, data, undefined, loading)
}

const validateConnection: (data: any, loading?: Ref<boolean>) => Promise<Result<any>> = (
  data,
  loading,
) => {
  return put(`${prefix}/source`, data, undefined, loading)
}
export default {
  getPlatformInfo,
  updateConfig,
  validateConnection,
}
