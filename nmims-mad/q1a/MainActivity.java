package com.example.productcsv;

import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;

public class MainActivity extends AppCompatActivity {

    private static final String FILE_NAME = "products.csv";

    EditText etId, etName, etPrice, etQty;
    TextView tvResult;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etId = findViewById(R.id.etId);
        etName = findViewById(R.id.etName);
        etPrice = findViewById(R.id.etPrice);
        etQty = findViewById(R.id.etQty);
        tvResult = findViewById(R.id.tvResult);
    }

    public void saveProduct(View v) {
        String id = etId.getText().toString().trim();
        String name = etName.getText().toString().trim();
        String price = etPrice.getText().toString().trim();
        String qty = etQty.getText().toString().trim();

        if (id.isEmpty() || name.isEmpty() || price.isEmpty() || qty.isEmpty()) {
            Toast.makeText(this, "Please fill all the fields", Toast.LENGTH_SHORT).show();
            return;
        }

        name = name.replace(",", " ");
        String line = id + "," + name + "," + price + "," + qty + "\n";

        try {
            FileOutputStream fos = openFileOutput(FILE_NAME, MODE_APPEND);
            fos.write(line.getBytes());
            fos.close();
            Toast.makeText(this, "Product saved", Toast.LENGTH_SHORT).show();
            etId.setText("");
            etName.setText("");
            etPrice.setText("");
            etQty.setText("");
        } catch (IOException e) {
            Toast.makeText(this, "Could not save: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    public void showAll(View v) {
        tvResult.setText(readFile(null));
    }

    public void searchById(View v) {
        String id = etId.getText().toString().trim();
        if (id.isEmpty()) {
            Toast.makeText(this, "Enter a product ID to search", Toast.LENGTH_SHORT).show();
            return;
        }
        tvResult.setText(readFile(id));
    }

    private String readFile(String searchId) {
        StringBuilder sb = new StringBuilder();
        try {
            BufferedReader br = new BufferedReader(new InputStreamReader(openFileInput(FILE_NAME)));
            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length < 4) continue;
                if (searchId == null || parts[0].equals(searchId)) {
                    sb.append("ID: ").append(parts[0])
                      .append("\nName: ").append(parts[1])
                      .append("\nPrice: Rs. ").append(parts[2])
                      .append("\nQuantity: ").append(parts[3])
                      .append("\n\n");
                }
            }
            br.close();
        } catch (FileNotFoundException e) {
            return "No products saved yet.";
        } catch (IOException e) {
            return "Error reading file: " + e.getMessage();
        }
        if (sb.length() == 0) return "No matching product found.";
        return sb.toString();
    }
}
