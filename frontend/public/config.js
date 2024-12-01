const BASE_URL_API_V1 = 'http://127.0.0.1:8000/api/v1/';
const BASE_URL = 'http://127.0.0.1:8000/';

const USERS_ENDPOINT = `${BASE_URL_API_V1}users`;
const REGISTER_ENDPOINT = `${BASE_URL}auth/register`;
const LOGIN_ENDPOINT = `${BASE_URL}auth/token`;
const EVENTS_USER = `${BASE_URL_API_V1}events/user/`;
const EVENTS = `${BASE_URL_API_V1}events/`;


const LOGIN_PAGE = `/`;
const REGISTER_PAGE = `/auth/register`;
const HOME_PAGE = '/init'


export {
  BASE_URL,
  BASE_URL_API_V1,
  USERS_ENDPOINT,
  LOGIN_PAGE,
  REGISTER_PAGE,
  REGISTER_ENDPOINT,
  LOGIN_ENDPOINT,
  HOME_PAGE,
  EVENTS_USER,
  EVENTS
};