param baseName string
param env string
param location string
param appServiceSku string
param acrName string
param acrResourceId string
param subnetId string
param keyVaultId string
param logAnalyticsId string

var namePrefix = '${baseName}-${env}'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${namePrefix}-asp'
  location: location
  sku: {
    name: appServiceSku
    tier: 'PremiumV3'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Managed Identities
resource backendIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-backend-mi'
  location: location
}

resource frontendIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-frontend-mi'
  location: location
}

// Backend Web App
resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${namePrefix}-backend'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${backendIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrName}.azurecr.io/fabric-customer360-backend:latest'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: backendIdentity.properties.clientId
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      vnetRouteAllEnabled: true
      appSettings: [
        {
          name: 'KEYVAULT_URL'
          value: reference(keyVaultId, '2023-07-01').vaultUri
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
      ]
    }
    virtualNetworkSubnetId: subnetId
  }
}

// Frontend Web App
resource frontendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${namePrefix}-frontend'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${frontendIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrName}.azurecr.io/fabric-customer360-frontend:latest'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: frontendIdentity.properties.clientId
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      vnetRouteAllEnabled: true
      appSettings: [
        {
          name: 'BACKEND_URL'
          value: 'https://${backendApp.properties.defaultHostName}'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
      ]
    }
    virtualNetworkSubnetId: subnetId
  }
}

// RBAC: Backend Identity -> ACR Pull
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrResourceId, 'AcrPull', backendIdentity.id)
  scope: resourceId('Microsoft.ContainerRegistry/registries', acrName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: backendIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Frontend Identity -> ACR Pull
resource acrPullRoleFrontend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrResourceId, 'AcrPull', frontendIdentity.id)
  scope: resourceId('Microsoft.ContainerRegistry/registries', acrName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: frontendIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Backend Identity -> Key Vault Secrets User
resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultId, 'KVSecretsUser', backendIdentity.id)
  scope: resourceId('Microsoft.KeyVault/vaults', split(keyVaultId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: backendIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output backendAppName string = backendApp.name
output frontendAppName string = frontendApp.name
output backendUrl string = 'https://${backendApp.properties.defaultHostName}'
output frontendUrl string = 'https://${frontendApp.properties.defaultHostName}'
output backendIdentityClientId string = backendIdentity.properties.clientId
output frontendIdentityClientId string = frontendIdentity.properties.clientId
