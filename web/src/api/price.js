import request from '../utils/request'

export const getSummary = () =>
  request.get('/api/prices/summary')

export const getPriceList = (params) =>
  request.get('/api/prices/list', { params })

export const getCategories = () =>
  request.get('/api/prices/categories')

export const getPriceTrend = (params) =>
  request.get('/api/prices/trend', { params })

export const getTopProducts = () =>
  request.get('/api/prices/top-products')

export const getDailyAvg = () =>
  request.get('/api/prices/daily-avg')

export const getCategoryStats = () =>
  request.get('/api/prices/category-stats')

export const getTopExpensive = () =>
  request.get('/api/prices/top-expensive')

export const getTopCheapest = () =>
  request.get('/api/prices/top-cheapest')

export const getPriceVolatility = () =>
  request.get('/api/prices/price-volatility')

export const getMarketStats = () =>
  request.get('/api/prices/market-stats')

export const searchProducts = (keyword) =>
  request.get('/api/prices/products/search', { params: { keyword } })