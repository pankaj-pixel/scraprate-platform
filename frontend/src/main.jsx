import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import AdminPrices from './admin/AdminPrices';
import AdminImportPrices from './admin/AdminImportPrices';
import AdminPriceSubmissions from './admin/AdminPriceSubmissions';
import SubmitPrice from './admin/SubmitPrice';
import AdminDataSources from './admin/AdminDataSources';
import ScrapPricesPage from './public/ScrapPricesPage';
import MaterialPricePage from './public/MaterialPricePage';
import StaticPage from './public/StaticPage';
import NotFoundPage from './public/NotFoundPage';
import { initializeAnalytics } from './analytics';
import AdminAnalytics from './admin/AdminAnalytics';

const path = window.location.pathname.replace(/\/$/, '');
const materialMatch = path.match(/^\/scrap-price\/([a-z0-9-]+)$/);
const publicPages = ['about','contact','methodology','sources','disclaimer','privacy','terms'];
const Page = path === '' ? App : path === '/admin/prices' ? AdminPrices : path === '/admin/import-prices' ? AdminImportPrices : path === '/admin/price-submissions' ? AdminPriceSubmissions : path === '/admin/data-sources' ? AdminDataSources : path === '/admin/analytics' ? AdminAnalytics : path === '/submit-price' ? SubmitPrice : path === '/scrap-prices' ? ScrapPricesPage : materialMatch ? () => <MaterialPricePage slug={materialMatch[1]} /> : publicPages.includes(path.slice(1)) ? () => <StaticPage page={path.slice(1)}/> : NotFoundPage;

initializeAnalytics();

ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><Page /></React.StrictMode>);
