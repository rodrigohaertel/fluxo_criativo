const { notarize } = require('@electron/notarize');

exports.default = async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;

  if (electronPlatformName !== 'darwin') return;

  const appleId = process.env.APPLE_ID;
  const appleTeamId = process.env.APPLE_TEAM_ID;
  const appleIdPassword = process.env.APPLE_APP_SPECIFIC_PASSWORD;

  if (!appleId || !appleTeamId || !appleIdPassword) {
    console.log('Variáveis de notarização não encontradas. Pulando notarização.');
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = `${appOutDir}/${appName}.app`;

  console.log(`Notarizando ${appPath}...`);

  await notarize({
    tool: 'notarytool',
    appPath,
    appleId,
    appleIdPassword,
    teamId: appleTeamId,
  });

  console.log('Notarização concluída.');
};
