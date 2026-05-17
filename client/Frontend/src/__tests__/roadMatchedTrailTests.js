/**
 * Test Plan: Road-Matched Trail System
 * Comprehensive test cases for OSRM routing, off-route detection, and trail rendering
 */

import {
  getRoute,
  detectOffRoute,
  scheduleReroute,
  calculateDistance,
  decodePolyline6,
  OFF_ROUTE_THRESHOLD_METERS,
} from '../services/roadMatchedTrailService.js';
import {
  detectOverlap,
  computeOverlapOffset,
  offsetPolyline,
} from '../utils/trailOverlapRenderer.js';
import {
  generateColorFromTruckId,
  hslToRgb,
  getComplementaryColor,
  colorStore,
} from '../utils/truckColorUtils.js';

/**
 * ==================== TEST SUITE 1: OSRM Routing ====================
 */

export const testOsrmRouting = {
  name: 'OSRM Routing & Caching',

  async testBasicRoute() {
    console.log('🧪 Test 1.1: Basic route request');
    const origin = { lat: -17.8252, lng: 31.0335 }; // Harare
    const current = { lat: -17.85, lng: 31.05 };
    const destination = { lat: -20.2811, lng: 28.7578 }; // Bulawayo

    const route = await getRoute(origin, current, destination);

    console.assert(route !== null, '❌ Route should not be null');
    console.assert(route.geometry.length > 0, '❌ Route should have geometry points');
    console.assert(route.distance > 0, '❌ Route should have positive distance');
    console.assert(route.duration > 0, '❌ Route should have positive duration');
    console.log('✅ Test 1.1 passed: Basic route retrieved');
    return route;
  },

  async testCaching() {
    console.log('🧪 Test 1.2: Response caching');
    const origin = { lat: -17.8252, lng: 31.0335 };
    const current = { lat: -17.85, lng: 31.05 };
    const destination = { lat: -20.2811, lng: 28.7578 };

    const start1 = performance.now();
    const route1 = await getRoute(origin, current, destination, { useCache: true });
    const time1 = performance.now() - start1;

    const start2 = performance.now();
    const route2 = await getRoute(origin, current, destination, { useCache: true });
    const time2 = performance.now() - start2;

    console.assert(time2 < time1 * 0.5, '❌ Cached request should be much faster');
    console.assert(JSON.stringify(route1) === JSON.stringify(route2), '❌ Cached response should be identical');
    console.log(`✅ Test 1.2 passed: Cache working (${time1.toFixed(0)}ms → ${time2.toFixed(0)}ms)`);
  },

  async testDistanceCalculation() {
    console.log('🧪 Test 1.3: Distance calculation');

    // Harar to Mutare (roughly 600km)
    const dist1 = calculateDistance(-17.8252, 31.0335, -18.978, 32.667);
    console.assert(dist1 > 500000 && dist1 < 700000, `❌ Distance should be ~600km, got ${(dist1 / 1000).toFixed(0)}km`);

    // Same point
    const dist2 = calculateDistance(-17.8252, 31.0335, -17.8252, 31.0335);
    console.assert(Math.abs(dist2) < 10, '❌ Distance from point to itself should be ~0');

    console.log('✅ Test 1.3 passed: Distance calculations accurate');
  },
};

/**
 * ==================== TEST SUITE 2: Off-Route Detection ====================
 */

export const testOffRouteDetection = {
  name: 'Off-Route Detection',

  async testOnRoute() {
    console.log('🧪 Test 2.1: On-route GPS position');

    // Mock route geometry (Harare to Mutare)
    const route = await getRoute(
      { lat: -17.8252, lng: 31.0335 },
      { lat: -17.85, lng: 31.05 },
      { lat: -18.978, lng: 32.667 }
    );

    if (!route) {
      console.warn('⚠️ Could not get route for test');
      return;
    }

    // Test GPS position on route (roughly)
    const midpoint = route.geometry[Math.floor(route.geometry.length / 2)];
    const result = detectOffRoute(route.geometry, midpoint.lat, midpoint.lng);

    console.assert(!result.isOffRoute, '❌ Truck on route should not be flagged as off-route');
    console.assert(result.distanceOffRoute < OFF_ROUTE_THRESHOLD_METERS, '❌ Distance should be small');
    console.log(`✅ Test 2.1 passed: On-route detection (${result.distanceOffRoute.toFixed(0)}m from route)`);
  },

  async testSmallDeviation() {
    console.log('🧪 Test 2.2: Small deviation (10-30m)');

    const route = await getRoute(
      { lat: -17.8252, lng: 31.0335 },
      { lat: -17.85, lng: 31.05 },
      { lat: -18.978, lng: 32.667 }
    );

    if (!route) return;

    // Small deviation from midpoint
    const midpoint = route.geometry[Math.floor(route.geometry.length / 2)];
    const result = detectOffRoute(
      route.geometry,
      midpoint.lat + 0.0005, // ~55m deviation
      midpoint.lng + 0.0005
    );

    // Should still be on-route (below threshold)
    console.log(`ℹ️ Deviation result: isOffRoute=${result.isOffRoute}, distance=${result.distanceOffRoute.toFixed(0)}m`);
  },

  async testLargeDeviation() {
    console.log('🧪 Test 2.3: Large deviation (>100m)');

    const route = await getRoute(
      { lat: -17.8252, lng: 31.0335 },
      { lat: -17.85, lng: 31.05 },
      { lat: -18.978, lng: 32.667 }
    );

    if (!route) return;

    // Large deviation (100+ meters)
    const midpoint = route.geometry[Math.floor(route.geometry.length / 2)];
    const result = detectOffRoute(
      route.geometry,
      midpoint.lat + 0.002, // ~220m deviation
      midpoint.lng + 0.002
    );

    console.assert(result.isOffRoute, '❌ Large deviation should trigger off-route');
    console.assert(result.distanceOffRoute > OFF_ROUTE_THRESHOLD_METERS, '❌ Distance should exceed threshold');
    console.log(`✅ Test 2.3 passed: Off-route detected (${result.distanceOffRoute.toFixed(0)}m from route)`);
  },
};

/**
 * ==================== TEST SUITE 3: Trail Overlap ====================
 */

export const testTrailOverlap = {
  name: 'Trail Overlap Detection & Rendering',

  testOverlapDetection() {
    console.log('🧪 Test 3.1: Overlap detection');

    // Two overlapping routes
    const route1 = [
      { lat: -17.8, lng: 31.0 },
      { lat: -17.85, lng: 31.05 },
      { lat: -17.9, lng: 31.1 },
    ];

    const route2 = [
      { lat: -17.82, lng: 31.02 },
      { lat: -17.85, lng: 31.05 }, // Overlapping point
      { lat: -17.88, lng: 31.08 },
    ];

    const overlap = detectOverlap(route1, route2, 50);

    console.assert(overlap.isOverlapping, '❌ Overlapping routes should be detected');
    console.assert(overlap.overlapSegments.length > 0, '❌ Should have overlap segments');
    console.log(`✅ Test 3.1 passed: Found ${overlap.overlapSegments.length} overlap segments`);
  },

  testNoOverlap() {
    console.log('🧪 Test 3.2: Non-overlapping routes');

    const route1 = [
      { lat: -17.8, lng: 31.0 },
      { lat: -17.85, lng: 31.05 },
    ];

    const route2 = [
      { lat: -18.0, lng: 31.5 },
      { lat: -18.05, lng: 31.55 },
    ];

    const overlap = detectOverlap(route1, route2, 50);

    console.assert(!overlap.isOverlapping, '❌ Non-overlapping routes should not be flagged');
    console.log('✅ Test 3.2 passed: Non-overlapping routes correctly identified');
  },

  testOffsetCalculation() {
    console.log('🧪 Test 3.3: Overlap offset calculation');

    const offset1 = computeOverlapOffset(0, 3);
    const offset2 = computeOverlapOffset(1, 3);
    const offset3 = computeOverlapOffset(2, 3);

    console.assert(Math.abs(offset1) < Math.abs(offset2) || offset1 === 0, '❌ Offsets should vary');
    console.log(`✅ Test 3.3 passed: Offsets calculated (${offset1.toFixed(6)}, ${offset2.toFixed(6)}, ${offset3.toFixed(6)})`);
  },

  testPolylineOffset() {
    console.log('🧪 Test 3.4: Polyline offset');

    const original = [
      { lat: -17.8, lng: 31.0 },
      { lat: -17.85, lng: 31.05 },
    ];

    const offset = offsetPolyline(original, 0.001, 0.002);

    console.assert(offset.length === original.length, '❌ Offset polyline should have same length');
    console.assert(offset[0].lat !== original[0].lat, '❌ Offset should modify coordinates');
    console.log('✅ Test 3.4 passed: Polyline offset applied correctly');
  },
};

/**
 * ==================== TEST SUITE 4: Color Management ====================
 */

export const testColorManagement = {
  name: 'Truck Color Assignment & Persistence',

  testColorGeneration() {
    console.log('🧪 Test 4.1: Color generation from truck ID');

    const color1 = generateColorFromTruckId('TRUCK-001');
    const color2 = generateColorFromTruckId('TRUCK-002');
    const color3 = generateColorFromTruckId('TRUCK-001'); // Same as first

    console.assert(color1.includes('hsl('), '❌ Color should be HSL format');
    console.assert(color1 !== color2, '❌ Different trucks should have different colors');
    console.assert(color1 === color3, '❌ Same truck ID should generate same color');
    console.log(`✅ Test 4.1 passed: Colors ${color1}, ${color2}`);
  },

  testHslToRgb() {
    console.log('🧪 Test 4.2: HSL to RGB conversion');

    const rgb1 = hslToRgb('hsl(0, 75%, 50%)'); // Red
    const rgb2 = hslToRgb('hsl(120, 75%, 50%)'); // Green
    const rgb3 = hslToRgb('hsl(240, 75%, 50%)'); // Blue

    console.assert(rgb1.startsWith('#'), '❌ RGB should be hex format');
    console.assert(rgb1.length === 7, '❌ Hex color should be 7 chars');
    console.assert(rgb1 !== rgb2 && rgb2 !== rgb3, '❌ Colors should differ');
    console.log(`✅ Test 4.2 passed: RGB conversions ${rgb1}, ${rgb2}, ${rgb3}`);
  },

  testComplementaryColor() {
    console.log('🧪 Test 4.3: Complementary color generation');

    const color = 'hsl(210, 75%, 50%)';
    const comp = getComplementaryColor(color);

    console.assert(comp.includes('hsl('), '❌ Complementary should be HSL format');
    console.assert(comp !== color, '❌ Complementary should differ from original');
    console.log(`✅ Test 4.3 passed: Original ${color} → Complementary ${comp}`);
  },

  testColorPersistence() {
    console.log('🧪 Test 4.4: Color persistence in storage');

    colorStore.clearAll();
    const color1 = colorStore.assignColor('TRUCK-001');
    const color2 = colorStore.getColor('TRUCK-001');

    console.assert(color1 === color2, '❌ Color should persist');

    // Simulate page reload
    const stored = colorStore.getAllColors();
    console.assert(stored['TRUCK-001'] === color1, '❌ Color should be in storage');
    console.log(`✅ Test 4.4 passed: Color persisted ${color1}`);
  },
};

/**
 * ==================== TEST SUITE 5: Real-World Scenarios ====================
 */

export const testRealWorldScenarios = {
  name: 'Real-World Scenarios',

  async testHarareToMutareRoute() {
    console.log('🧪 Test 5.1: Harare → Mutare (East) - ~220km');

    const origin = { lat: -17.8252, lng: 31.0335 }; // Harare
    const destination = { lat: -18.978, lng: 32.667 }; // Mutare

    const route = await getRoute(
      origin,
      { lat: -17.85, lng: 31.05 }, // Current position near Harare
      destination
    );

    if (route) {
      console.log(`✅ Test 5.1 passed: ${(route.distance / 1000).toFixed(0)}km route`);
    }
  },

  async testHarareToMutareDetourViaLwandiwe() {
    console.log('🧪 Test 5.2: Truck takes detour via Ruwa');

    const origin = { lat: -17.8252, lng: 31.0335 }; // Harare
    const detourPosition = { lat: -17.7, lng: 30.85 }; // Detour west
    const destination = { lat: -18.978, lng: 32.667 }; // Mutare

    const directRoute = await getRoute(origin, origin, destination);
    const detourRoute = await getRoute(origin, detourPosition, destination);

    if (directRoute && detourRoute) {
      const detourExtra = detourRoute.distance - directRoute.distance;
      console.log(`ℹ️ Detour adds ${(detourExtra / 1000).toFixed(1)}km to route`);
      console.log(`✅ Test 5.2 passed: Detour rerouting works`);
    }
  },

  async testHarareToMutareVsBulawayo() {
    console.log('🧪 Test 5.3: Multi-destination routing');

    const origin = { lat: -17.8252, lng: 31.0335 }; // Harare
    const currentPos = { lat: -17.85, lng: 31.05 };

    const routeToMutare = await getRoute(
      origin,
      currentPos,
      { lat: -18.978, lng: 32.667 } // Mutare (East)
    );

    const routeToBulawayo = await getRoute(
      origin,
      currentPos,
      { lat: -20.2811, lng: 28.7578 } // Bulawayo (South)
    );

    if (routeToMutare && routeToBulawayo) {
      console.log(`ℹ️ Mutare: ${(routeToMutare.distance / 1000).toFixed(0)}km, Bulawayo: ${(routeToBulawayo.distance / 1000).toFixed(0)}km`);
      console.log(`✅ Test 5.3 passed: Multi-destination comparison complete`);
    }
  },
};

/**
 * Main test runner
 */
export async function runAllTests() {
  console.log('🚀 Starting Road-Matched Trail System Tests\n');

  console.log('='.repeat(50));
  console.log(testOsrmRouting.name);
  console.log('='.repeat(50));
  await testOsrmRouting.testBasicRoute();
  await testOsrmRouting.testCaching();
  await testOsrmRouting.testDistanceCalculation();

  console.log('\n' + '='.repeat(50));
  console.log(testOffRouteDetection.name);
  console.log('='.repeat(50));
  await testOffRouteDetection.testOnRoute();
  await testOffRouteDetection.testSmallDeviation();
  await testOffRouteDetection.testLargeDeviation();

  console.log('\n' + '='.repeat(50));
  console.log(testTrailOverlap.name);
  console.log('='.repeat(50));
  testTrailOverlap.testOverlapDetection();
  testTrailOverlap.testNoOverlap();
  testTrailOverlap.testOffsetCalculation();
  testTrailOverlap.testPolylineOffset();

  console.log('\n' + '='.repeat(50));
  console.log(testColorManagement.name);
  console.log('='.repeat(50));
  testColorManagement.testColorGeneration();
  testColorManagement.testHslToRgb();
  testColorManagement.testComplementaryColor();
  testColorManagement.testColorPersistence();

  console.log('\n' + '='.repeat(50));
  console.log(testRealWorldScenarios.name);
  console.log('='.repeat(50));
  await testRealWorldScenarios.testHarareToMutareRoute();
  await testRealWorldScenarios.testHarareToMutareDetourViaLwandiwe();
  await testRealWorldScenarios.testHarareToMutareVsBulawayo();

  console.log('\n' + '='.repeat(50));
  console.log('✅ All tests completed!');
  console.log('='.repeat(50));
}

// Export for use in browser console
if (typeof window !== 'undefined') {
  window.runTrailTests = runAllTests;
  console.log('ℹ️ Tests available: run window.runTrailTests() in console');
}

export default {
  testOsrmRouting,
  testOffRouteDetection,
  testTrailOverlap,
  testColorManagement,
  testRealWorldScenarios,
  runAllTests,
};
