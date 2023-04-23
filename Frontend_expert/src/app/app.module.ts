import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http'; // Import HttpClientModule
import { FormsModule, ReactiveFormsModule } from '@angular/forms'; // Import ReactiveFormsModule
import { AppComponent } from './app.component';
import { UploadFileComponent } from './file-upload/file-upload.component';
import { RouterModule } from '@angular/router';
import { DataPreprocessingComponent } from './data-preprocessing/data-preprocessing.component';
import { AppRoutingModule } from './app-routing.module';
import { NgChartsModule } from 'ng2-charts';
import { DatavisualisationComponent } from './datavisualisation/datavisualisation.component';
import { DataProcessingComponent } from './data-processing/data-processing.component';

@NgModule({
  declarations: [
    AppComponent,
    UploadFileComponent,
    DataPreprocessingComponent,
    DatavisualisationComponent,
    DataProcessingComponent,
      ],
  imports: [
    BrowserModule,
    HttpClientModule,
    ReactiveFormsModule ,
    FormsModule, 
    RouterModule,
    AppRoutingModule ,
    NgChartsModule,
    
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
