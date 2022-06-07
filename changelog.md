# PEON ORC - Changelog

## 0.2.13-dev

- Scheduler - v1.0 - Added simple start & delayed stop in scheduler

## 0.2.12-dev

- API Response - Server config

## 0.2.11-dev

- PUBLIC_IP - added to container variables

## 0.2.10-dev

- Logging - Added devMode switch

## 0.2.9-dev

- UI - Added MOTD to container login

## 0.2.8-dev

- Base Image Update - Base images were repulled to get latest versions & app rebuilt on those
- BugFix: Incorrect parameter reference in server create
  
## 0.2.7-dev

- Security - Inital CORS implementation
- Security - Initial api-key requirement implementation

## 0.2.6-dev

- API - Server - Destroy & Eradicate

## 0.2.5-dev

- API - Server - Reworked to include actions into path
- API - Server - Added get with metrics

## 0.2.4-dev

- API - Server Get - reworked to provide both container & server state

## 0.2.3-dev

- API - Auto download latest plan version when server is deployed
  
## 0.2.2-dev

- API - Plans get list & update from Peon project list

## 0.2.1-dev

- Bugfix - Enforced description & settings on [post]servers
  
## 0.2.0-dev

- Added custom config handler
- Allows configuration of environment variables in container (via API)
- Can supply json/txt files via API
- Added persistent description

## 0.1.6-dev

- Added handler for ``config`` folder
- Moved game server logs into game server directory

## 0.1.5-dev

- First iteration of server create (API)
