import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const API_URL = 'http://localhost:8000/api/v1';

async function testTruckCreation() {
  try {
    const truckData = {
      fleet_id: uuidv4(),
      truck_identifier: 'TEST-API-TRUCK',
      plate: 'TEST-API-' + Date.now(),
      make: 'TestMake',
      model: 'TestModel',
      year: 2024,
      vin: 'TEST-VIN-' + Date.now(),
      telematics_id: 'TEST-TEL',
      fuel_capacity_liters: 100,
      status: 'IDLE'
    };

    console.log('📤 Sending truck creation request to:', API_URL + '/trucks/');
    console.log('📋 Data:', JSON.stringify(truckData, null, 2));

    const response = await axios.post(API_URL + '/trucks/', truckData, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });

    console.log('✅ Success! Status:', response.status);
    console.log('📦 Response data:', JSON.stringify(response.data, null, 2));
    console.log('Truck created with ID:', response.data.fleet_id);
  } catch (error) {
    console.error('❌ Error creating truck');
    console.error('  Status:', error.response?.status);
    console.error('  Status Text:', error.response?.statusText);
    console.error('  Data:', error.response?.data);
    console.error('  Message:', error.message);
  }
}

testTruckCreation();
