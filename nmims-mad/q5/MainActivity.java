package com.example.placefinder;

import android.location.Address;
import android.location.Geocoder;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.google.android.gms.maps.CameraUpdateFactory;
import com.google.android.gms.maps.GoogleMap;
import com.google.android.gms.maps.OnMapReadyCallback;
import com.google.android.gms.maps.SupportMapFragment;
import com.google.android.gms.maps.model.LatLng;
import com.google.android.gms.maps.model.MarkerOptions;

import java.io.IOException;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity implements OnMapReadyCallback {

    GoogleMap myMap;
    EditText etPlace;
    Button btnSearch;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etPlace = findViewById(R.id.etPlace);
        btnSearch = findViewById(R.id.btnSearch);

        SupportMapFragment mapFragment =
                (SupportMapFragment) getSupportFragmentManager().findFragmentById(R.id.map);
        mapFragment.getMapAsync(this);

        btnSearch.setOnClickListener(v -> searchPlace());
    }

    @Override
    public void onMapReady(GoogleMap googleMap) {
        myMap = googleMap;
        myMap.getUiSettings().setZoomControlsEnabled(true);

        // start with Mumbai on the screen
        LatLng mumbai = new LatLng(19.0760, 72.8777);
        myMap.moveCamera(CameraUpdateFactory.newLatLngZoom(mumbai, 10));
    }

    private void searchPlace() {
        String place = etPlace.getText().toString().trim();
        if (place.isEmpty()) {
            Toast.makeText(this, "Enter a place name", Toast.LENGTH_SHORT).show();
            return;
        }

        Geocoder geocoder = new Geocoder(this, Locale.getDefault());
        try {
            // converts the name into latitude and longitude
            List<Address> list = geocoder.getFromLocationName(place, 1);
            if (list == null || list.isEmpty()) {
                Toast.makeText(this, "Place not found", Toast.LENGTH_SHORT).show();
                return;
            }

            Address address = list.get(0);
            LatLng point = new LatLng(address.getLatitude(), address.getLongitude());

            myMap.clear();
            myMap.addMarker(new MarkerOptions().position(point).title(place));
            myMap.animateCamera(CameraUpdateFactory.newLatLngZoom(point, 15));
        } catch (IOException e) {
            Toast.makeText(this, "Network problem, try again", Toast.LENGTH_SHORT).show();
        }
    }
}
