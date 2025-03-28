// const back_port = process.env.BACK;
// console.log(back_port)
const BASE_URL_API_V1 = 'http://localhost:8000/api/v1/';
const BASE_URL = 'http://localhost:8000/';

const USERS_ENDPOINT = `${BASE_URL_API_V1}users`;
const REGISTER_ENDPOINT = `${BASE_URL}auth/register`;
const LOGIN_ENDPOINT = `${BASE_URL}auth/token`;
const EVENTS_USER = `${BASE_URL_API_V1}events/user/`;
const EVENTS = `${BASE_URL_API_V1}events/`;
const MEETINGS = `${BASE_URL_API_V1}meetings/user/`;
const MEETING = `${BASE_URL_API_V1}meetings/`;
const GROUPS = `${BASE_URL_API_V1}groups/`;
const GROUPS_INVITATIONS = `${BASE_URL_API_V1}groups/users/invited_groups`


const LOGIN_PAGE = `/`;
const REGISTER_PAGE = `/auth/register`;
const HOME_PAGE = '/init'
const GROUP_PAGE = 'group'


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
  EVENTS,
  MEETINGS,
  MEETING,
  GROUP_PAGE,
  GROUPS,
  GROUPS_INVITATIONS
};