odoo.define('dental_clinic.PatientAppointmentToothChart', function(require) {
   "use strict";

   const { Component, useState, onMounted, onWillStart, useRef } = owl;
   const { useService } = require("@web/core/utils/hooks");

   class PatientAppointmentToothChart extends Component {
       static template = "PatientAppointmentFormToothChart";
       
       setup() {
           this.orm = useService("orm");
           this.rpc = useService("rpc");
           this.notification = useService("notification");
           
           this.state = useState({
               markedTeeth: [],
               teethData: []
           });

           this.chartRef = useRef("toothChart");

           onWillStart(async () => {
               await this.loadInitialData();
           });

           onMounted(() => {
               this.setupTeethInteractions();
               this.updateChartMarks();
               this.setupUpdateButton();
           });
       }

       async loadInitialData() {
           try {
               if (!this.props.appointmentId) return;
               
               const teethData = await this.rpc({
                   model: 'dental.procedure.line',
                   method: 'search_read',
                   fields: ['tooth_number', 'procedure_id'],
                   domain: [['appointment_id', '=', this.props.appointmentId]]
               });
               
               this.state.teethData = teethData;
               // Convert to string to match SVG IDs
               this.state.markedTeeth = teethData.map(item => item.tooth_number.toString());
           } catch (error) {
               console.error("Error loading teeth data:", error);
               this.notification.add(
                   this.env._t("Error loading dental data"),
                   { type: 'danger' }
               );
           }
       }

       setupTeethInteractions() {
           const chartElement = this.chartRef.el;
           if (!chartElement) return;

           // Usamos delegación de eventos para mejor rendimiento
           chartElement.addEventListener('click', (event) => {
               const toothElement = event.target.closest('polygon, path');
               if (!toothElement || !toothElement.id) return;
               
               this.toggleToothMark(toothElement.id, toothElement);
           });
       }

       setupUpdateButton() {
           const button = this.chartRef.el.querySelector('#update-toothChart-button');
           if (button) {
               button.addEventListener('click', () => this.updateProcedures());
           }
       }

       toggleToothMark(toothNumber, element) {
           const index = this.state.markedTeeth.indexOf(toothNumber);
           
           if (index >= 0) {
               this.state.markedTeeth.splice(index, 1);
               element?.classList.remove("marked");
           } else {
               this.state.markedTeeth.push(toothNumber);
               element?.classList.add("marked");
           }
       }

       updateChartMarks() {
           const chartElement = this.chartRef.el;
           if (!chartElement) return;
           
           // Actualizar todos los elementos del gráfico
           const toothElements = chartElement.querySelectorAll('polygon, path');
           toothElements.forEach(element => {
               if (element.id && this.state.markedTeeth.includes(element.id)) {
                   element.classList.add("marked");
               } else {
                   element.classList.remove("marked");
               }
           });
       }

       async updateProcedures() {
           try {
               if (!this.props.appointmentId) {
                   this.notification.add(
                       this.env._t("No appointment selected"),
                       { type: 'warning' }
                   );
                   return;
               }
               
               await this.rpc({
                   model: 'patient.appointment',
                   method: 'update_procedures',
                   args: [this.props.appointmentId, this.state.markedTeeth]
               });
               
               this.notification.add(
                   this.env._t("Dental chart updated successfully"),
                   { type: 'success' }
               );
               
               // Recargar datos para sincronización
               await this.loadInitialData();
               this.updateChartMarks();
           } catch (error) {
               console.error("Error updating procedures:", error);
               this.notification.add(
                   this.env._t("Error updating dental procedures"),
                   { type: 'danger' }
               );
           }
       }

       async resetChart() {
           this.state.markedTeeth = [];
           this.updateChartMarks();
           await this.updateProcedures();
       }
   }

   return PatientAppointmentToothChart;
});