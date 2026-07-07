/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TenantDto } from './TenantDto';
export type TenantListDto = {
  tenants: Array<TenantDto>;
  skip: number;
  limit: number;
  total: number;
  has_previous: boolean;
  has_next: boolean;
};

