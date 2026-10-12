package com.example.datetimedemo;

import android.os.Bundle;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.TextView;
import android.widget.TimePicker;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    DatePicker datePicker;
    TimePicker timePicker;
    Button btnShow;
    TextView tvResult;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        datePicker = findViewById(R.id.datePicker);
        timePicker = findViewById(R.id.timePicker);
        btnShow = findViewById(R.id.btnShow);
        tvResult = findViewById(R.id.tvResult);

        btnShow.setOnClickListener(v -> {
            int day = datePicker.getDayOfMonth();
            int month = datePicker.getMonth() + 1;
            int year = datePicker.getYear();

            int hour = timePicker.getHour();
            int minute = timePicker.getMinute();

            String amPm = (hour >= 12) ? "PM" : "AM";
            int hour12 = hour % 12;
            if (hour12 == 0) hour12 = 12;

            String date = day + "/" + month + "/" + year;
            String time = String.format("%02d:%02d %s", hour12, minute, amPm);

            tvResult.setText("Selected Date: " + date + "\nSelected Time: " + time);
        });
    }
}
