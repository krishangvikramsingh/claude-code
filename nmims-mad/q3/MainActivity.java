package com.example.datetimedemo;

import android.app.DatePickerDialog;
import android.app.TimePickerDialog;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.util.Calendar;

public class MainActivity extends AppCompatActivity {

    Button btnDate, btnTime, btnShow;
    TextView tvDate, tvTime, tvResult;

    int year, month, day, hour, minute;
    boolean dateSelected = false;
    boolean timeSelected = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnDate = findViewById(R.id.btnDate);
        btnTime = findViewById(R.id.btnTime);
        btnShow = findViewById(R.id.btnShow);
        tvDate = findViewById(R.id.tvDate);
        tvTime = findViewById(R.id.tvTime);
        tvResult = findViewById(R.id.tvResult);

        Calendar now = Calendar.getInstance();
        year = now.get(Calendar.YEAR);
        month = now.get(Calendar.MONTH);
        day = now.get(Calendar.DAY_OF_MONTH);
        hour = now.get(Calendar.HOUR_OF_DAY);
        minute = now.get(Calendar.MINUTE);

        btnDate.setOnClickListener(v -> {
            DatePickerDialog dialog = new DatePickerDialog(this,
                    (view, y, m, d) -> {
                        year = y;
                        month = m;
                        day = d;
                        dateSelected = true;
                        tvDate.setText("Date: " + String.format("%02d-%02d-%d", day, month + 1, year));
                    }, year, month, day);
            dialog.show();
        });

        btnTime.setOnClickListener(v -> {
            TimePickerDialog dialog = new TimePickerDialog(this,
                    (view, h, min) -> {
                        hour = h;
                        minute = min;
                        timeSelected = true;
                        tvTime.setText("Time: " + String.format("%02d:%02d", hour, minute));
                    }, hour, minute, true);
            dialog.show();
        });

        btnShow.setOnClickListener(v -> {
            if (!dateSelected || !timeSelected) {
                Toast.makeText(this, "Please select date and time first", Toast.LENGTH_SHORT).show();
                return;
            }
            String date = String.format("%02d-%02d-%d", day, month + 1, year);
            String time = String.format("%02d:%02d", hour, minute);
            tvResult.setText("Selected Date: " + date + "\nSelected Time: " + time);
        });
    }
}
