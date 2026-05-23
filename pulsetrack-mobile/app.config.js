const fs = require('fs');
const path = require('path');

// Load app.json and remove references to missing assets so Metro won't fail
const appJsonPath = path.join(__dirname, 'app.json');
let config = {};
try {
  config = require('./app.json').expo || {};
} catch (e) {
  console.warn('Failed to load app.json:', e && e.message);
}

// Ensure no icon or splash.image or adaptiveIcon.foregroundImage entries
if (config.icon) delete config.icon;
if (config.splash && config.splash.image) delete config.splash.image;
if (config.android && config.android.adaptiveIcon && config.android.adaptiveIcon.foregroundImage) {
  delete config.android.adaptiveIcon.foregroundImage;
}

module.exports = { expo: config };
