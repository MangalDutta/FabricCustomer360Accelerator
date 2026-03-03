targetScope = 'resourceGroup'

@description('Base name prefix for resources')
param baseName string

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, test, prod)')
param env string = 'dev'

@description('App Service plan SKU')
param appServiceSku string = 'P1v3'

@description('Container Registry SKU')
param acrSku string = 'Premium'

@description('Enable Application Insights and Log Analytics')
param enableMonitoring bool = true

var nameSuffix = '${baseName}-${env}'

// Networking
module networking 'modules/networking.bicep' = {
  name: 'deploy-networking'
  params: {
    baseName: baseName
    env: env
    location: location
  }
}

// Container Registry
module acr 'modules/acr.bicep' = {
  name: 'deploy-acr'
  params: {
    baseName: baseName
    env: env
    location: location
    acrSku: acrSku
    vnetId: networking.outputs.vnetId
    privateEndpointSubnetId: networking.outputs.privateEndpointSubnetId
  }
}

// Key Vault
module keyVault 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  params: {
    baseName: baseName
    env: env
    location: location
    vnetId: networking.outputs.vnetId
    privateEndpointSubnetId: networking.outputs.privateEndpointSubnetId
  }
}

// Monitoring (optional)
module monitoring 'modules/monitoring.bicep' = if (enableMonitoring) {
  name: 'deploy-monitoring'
  params: {
    baseName: baseName
    env: env
    location: location
  }
}

// App Services
module appServices 'modules/appservice.bicep' = {
  name: 'deploy-appservices'
  params: {
    baseName: baseName
    env: env
    location: location
    appServiceSku: appServiceSku
    acrName: acr.outputs.acrName
    acrResourceId: acr.outputs.acrId
    subnetId: networking.outputs.appSubnetId
    keyVaultId: keyVault.outputs.keyVaultId
    logAnalyticsId: enableMonitoring ? monitoring.outputs.logAnalyticsId : ''
  }
}

output acrName string = acr.outputs.acrName
output keyVaultName string = keyVault.outputs.keyVaultName
output backendAppName string = appServices.outputs.backendAppName
output frontendAppName string = appServices.outputs.frontendAppName
output backendUrl string = appServices.outputs.backendUrl
output frontendUrl string = appServices.outputs.frontendUrl
