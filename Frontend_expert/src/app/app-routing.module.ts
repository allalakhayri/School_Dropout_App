import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {UploadFileComponent} from './file-upload/file-upload.component';
import {DataPreprocessingComponent} from './data-preprocessing/data-preprocessing.component'
import {DatavisualisationComponent} from './datavisualisation/datavisualisation.component'
import {DataProcessingComponent} from './data-processing/data-processing.component'
const routes: Routes = [
  
  { path: 'upload', component: UploadFileComponent },
  { path: 'datapreprocessing', component: DataPreprocessingComponent },
  { path: 'datavisualisation', component: DatavisualisationComponent },
  {path: 'dataprocessing', component: DataProcessingComponent}

];

@NgModule({ 
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
