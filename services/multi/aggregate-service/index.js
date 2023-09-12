const express = require('express');

const app = express();

const ADMIN_URL = process.env.KONG_ADMIN_URL || 'http://localhost:8001/';
const PORT = process.env.PORT || 3333;

app.get('/healthcheck', (req, res) => {
  res.send('OK');
});

app.post('/sequence', async (req, res) => {
  let result = {};
  const serviceList = req.headers['service-list']; // [A, B, C]
  const response = await fetch(`${ADMIN_URL}/routes`);
  const routeList = await response.json().data;

  const validServices = routeList.filter((route) => serviceList.includes(route.name));
  for (const service of validServices) {
    const serviceUrl = service.url
      ? service.url
      : `${service.protocols[0]}://${service.hosts[0]}${service.path}`;

    const response = await fetch(serviceUrl);
    result[service] = await response.json().data;
  }

  return res.json(result);
});

app.post('/parallel', async (req, res) => {
  let result = {};
  const serviceList = req.headers['service-list']; // [A, B, C]
  const response = await fetch(`${ADMIN_URL}/routes`);
  const routeList = await response.json().data;

  const validServices = routeList.filter((route) => serviceList.includes(route.name));
  Promise.all(
    validServices.map(async (service) => {
      const serviceUrl = service.url
        ? service.url
        : `${service.protocols[0]}://${service.hosts[0]}${service.path}`;
      const response = await fetch(serviceUrl);
      if (response.ok) {
        result[service] = await response.json().data;
      }
    })
  );

  return res.json(result);
});

app.listen(8000, () => {
  console.log('Listening to port', PORT);
});
