import { DatePipe, formatDate } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Sort } from '@angular/material/sort';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { FilterPipe } from 'src/app/shared/filter.pipe';
import { AllInOneService } from 'src/app/shared/services/all-in-one.service';
import { KunyekService } from 'src/app/shared/services/kunyek.service';
import { MessageService } from 'src/app/shared/services/message.service';
import { SubSink } from 'subsink';

@Component({
  selector: 'app-timecard-report',
  templateUrl: './timecard-report.component.html',
  styleUrls: ['./timecard-report.component.scss'],
})
export class TimecardReportComponent implements OnInit, OnDestroy {
  mobileViewWidth: any = 426;
  isMobileView: boolean = false;
  isFocus: boolean = false;
  itemPerPage: number = 100;
  currentPage: number = 1;
  searchText: string = '';
  searchLoading: boolean = false;
  orgid: string = '';
  getList!: Subscription;

  timecardList: any = [];
  organizations: any = [];

  gettingMemberPosition: boolean = false;
  departmentList: string[] = ['All'];
  divisionList: string[] = ['All'];
  teamidList: string[] = ['All'];
  costCenterList: string[] = ['All'];
  subDivisionList: string[] = ['All'];
  monthlist: any[] = [];
  openfilter: boolean = false;
  getMemberSub!: Subscription;

  generalDatePickerConfig: any = this.allinoneService.datePickerConfig;

  currentDate = this.allinoneService.formatDBToShowInEdit(
    this.allinoneService.getCurrentDateToDB()
  );

  formatToShow = 'yyyy-MM-dd';
  dateRangeStartDate: any = '';
  minDate = new Date();
  date = new Date();
  firstDay = new Date(this.date.getFullYear(), this.date.getMonth(), 1);
  lastDay = new Date(this.date.getFullYear(), this.date.getMonth() + 1, 0);

  currentStartDate: any = this.datePipe.transform(this.firstDay, 'yyyy-MM-dd');
  currentEndDate: any = this.datePipe.transform(this.lastDay, 'yyyy-MM-dd');

  userStatusFilterList = this.allinoneService.userStatusFilterList;

  submitForm = {
    // date : this.currentDate,
    // enddate : this.lastDay,
    // startdate: this.currentStartDate,
    // enddate: this.currentEndDate,
    startdate: this.firstDay,
    enddate: this.lastDay,
    department: 'All',
    division: 'All',
    teamid: 'All',
    costcenter: 'All',
    subdivision: 'All',
    status : '001'
  };

  pg = [
    {
      name: '100 items',
      count: 100,
    },
    {
      name: '300 items',
      count: 300,
    },
    {
      name: '500 items',
      count: 500,
    },
  ];
  subscriptions = new SubSink();

  // websockect
  connectSocketLoading: boolean = true;
  private socket: WebSocket | undefined;
  public socketConnectionStatus: string = 'disconnected';
  public socketReceivedMessage: string = '';
  connectionId: string = '';
  drsocketfileurl: any = '';
  updateCId: boolean = false;
  socketConnectTime: any;
  totalWorkingHours: any;

  constructor(
    public allinoneService: AllInOneService,
    private kunyekService: KunyekService,
    private messageService: MessageService,
    private route: ActivatedRoute,
    private router: Router,
    private dialog: MatDialog,
    private filterPipe: FilterPipe,
    private datePipe: DatePipe,
    private http: HttpClient
  ) {
    if (!this.allinoneService.isAdminOf('hr')) {
      this.router.navigateByUrl('/hxm');
    }
  }

  ngOnInit(): void {
    var addDays = 35;
    this.dateRangeStartDate = this.currentStartDate;
    var maxEndDate = new Date(this.dateRangeStartDate);
    maxEndDate.setTime(maxEndDate.getTime() + addDays * 24 * 60 * 60 * 1000);
    // this.minDate = formatDate(
    //   maxEndDate,
    //   this.formatToShow,
    //   'en-US'
    // ).toString();
    this.minDate = maxEndDate;
    // this.monthlist = this.getCurrentAndPreviousYearMonths();
    this.organizations = this.allinoneService.orgs;
    this.orgid = this.allinoneService.selectedOrg
      ? this.allinoneService.selectedOrg
      : this.organizations[0].orgid;
  }

  test() {
    this.updateConnectionID();
  }

  ngOnDestroy(): void {
    this.socket?.close(3001);
    this.getList && this.getList.unsubscribe();
    this.getMemberSub && this.getMemberSub.unsubscribe();
    this.subscriptions.unsubscribe();
    clearTimeout(this.socketConnectTime);
  }

  dateChange() {
    var addDays = 35;
    this.dateRangeStartDate = this.submitForm.startdate;
    var maxEndDate = new Date(this.dateRangeStartDate);
    maxEndDate.setTime(maxEndDate.getTime() + addDays * 24 * 60 * 60 * 1000);
    // this.minDate = formatDate(
    //   maxEndDate,
    //   this.formatToShow,
    //   'en-US'
    // ).toString();
    this.minDate = maxEndDate;

    if (this.submitForm.enddate > this.minDate) {
      this.submitForm.enddate = this.minDate;
    }

    if (this.submitForm.enddate < this.submitForm.startdate) {
      this.submitForm.enddate = this.submitForm.startdate;
    }
  }

  search() {
    this.connectWebSocket();
    this.closeSocketWithTime();
  }

  updateConnectionID() {
    var data = {
      connectionid: this.connectionId,
      type: '004',
    };
    this.kunyekService.updateConnectionID(data).subscribe((res: any) => {
      console.log('id updated res');
      this.updateCId = false;
      console.log(res);
    });
  }

  connectWebSocket() {
    console.log('Calling Websocket');
    this.searchLoading = true;
    this.connectSocketLoading = true;
    const webSocketURL = this.allinoneService.attendanceSocketUrl;

    this.socket = new WebSocket(webSocketURL);

    this.socket.addEventListener('open', (event) => {
      console.log('WebSocket connection opened!');
      this.connectSocketLoading = false;
      // this.socket?.send('001');
      this.socketConnectionStatus = 'connected';
    });

    this.socket.addEventListener('message', (event) => {
      this.socketReceivedMessage = event.data;

      var tempData = JSON.parse(event.data);

      if (tempData.connectionId) {
        this.connectionId = tempData.connectionId;
        if (this.updateCId) {
          this.updateConnectionID();
        }
        this.getTimeCardReport();
      } else {
        this.drsocketfileurl = tempData.fileurl;

        if (this.drsocketfileurl) {
          this.http.get(this.drsocketfileurl).subscribe((res: any) => {
            console.log('Your get data res');
            console.log(res);
            this.timecardList = res;
            this.searchLoading = false;
            this.connectionId = '';
            this.socket?.close(3001);
            clearTimeout(this.socketConnectTime);
          });
        }
      }
    });

    this.socket.addEventListener('error', (event) => {
      console.error('WebSocket error:', event);
      this.socketConnectionStatus = 'error';
    });

    this.socket.addEventListener('close', (event) => {
      console.log('WebSocket connection closed!');
      console.log(event);
      this.socketConnectionStatus = 'disconnected';
      if (event.code != 3001) {
        this.connectionId = '';
        this.updateCId = true;
        this.connectWebSocket();
      }
    });
  }

  closeSocketWithTime() {
    this.socketConnectTime = setTimeout(() => {
      if (this.socketConnectionStatus != 'disconnected') {
        this.socket?.close(3001);
        this.connectionId = '';
        this.messageService.openSnackBar('Request Time Out', 'warn');
        this.searchLoading = false;
      }
    }, this.allinoneService.reportSocketTimeoutMins * 60 * 1000);
  }

  getTimeCardReport() {
    if (!this.submitForm.startdate) {
      return this.messageService.openSnackBar(
        'Start Date cannot be blank.',
        'warn'
      );
    }
    if (!this.submitForm.enddate) {
      return this.messageService.openSnackBar(
        'End Date cannot be blank.',
        'warn'
      );
    }
    this.searchLoading = true;
    var data = {
      orgid: this.orgid,
      date: '',
      startdate: this.allinoneService.parseDate(this.submitForm.startdate),
      enddate: this.allinoneService.parseDate(this.submitForm.enddate),
      department:
        !this.openfilter || this.submitForm.department == 'All'
          ? ''
          : this.submitForm.department,
      division:
        !this.openfilter || this.submitForm.division == 'All'
          ? ''
          : this.submitForm.division,
      teamid:
        !this.openfilter || this.submitForm.teamid == 'All'
          ? ''
          : this.submitForm.teamid,
      costcenter:
        !this.openfilter || this.submitForm.costcenter == 'All'
          ? ''
          : this.submitForm.costcenter,
      subdivision:
        !this.openfilter || this.submitForm.subdivision == 'All'
          ? ''
          : this.submitForm.subdivision,
          activestatus: this.submitForm.status,
      connectionid: this.connectionId,
    };
    // console.log(data);
    // return
    this.getList && this.getList.unsubscribe();
    this.getList = this.kunyekService.getTimecardReport(data).subscribe(
      (res: any) => {
        console.log(res);
        if (res.returncode == '300') {
          // this.timecardList = res.datalist;
          this.timecardList = res.whlist;
          this.totalWorkingHours = res.total_working_hours;
          this.searchLoading = false;
        } else {
          this.messageService.openSnackBar(
            res.message || res.status || 'Server Error',
            'warn'
          );
          this.searchLoading = false;
        }
      },
      (err: any) => {
        this.messageService.openSnackBar('Server Error', 'warn');
        this.searchLoading = false;
      }
    );
  }

  toggleFilter() {
    if (
      this.departmentList.length < 2 
      // ||
      // this.divisionList.length < 2 ||
      // this.teamidList.length < 2 ||
      // this.costCenterList.length < 2 ||
      // this.subDivisionList.length < 2
    ) {
      this.getMemberPosition();
    }
    this.openfilter = !this.openfilter;
  }

  departmentChange(dep: any) {
    if (this.submitForm.department != dep) {
      this.submitForm.department = dep;
      this.submitForm.division = 'All';
      this.submitForm.teamid = 'All';
      this.submitForm.costcenter = 'All';
      this.submitForm.subdivision = 'All';
    }
  }

  divisionChange(divi: any) {
    if (this.submitForm.division != divi) {
      this.submitForm.division = divi;
      this.submitForm.teamid = 'All';
      this.submitForm.costcenter = 'All';
      this.submitForm.subdivision = 'All';
    }
  }

  teamidChange(teamid: any) {
    if (this.submitForm.teamid != teamid) {
      this.submitForm.teamid = teamid;
      this.submitForm.costcenter = 'All';
      this.submitForm.subdivision = 'All';
    }
  }

  costCenterChange(costcenter: any) {
    if (this.submitForm.costcenter != costcenter) {
      this.submitForm.costcenter = costcenter;
      this.submitForm.subdivision = 'All';
    }
  }

  subDivisionChange(subdivision: any) {
    if (this.submitForm.subdivision != subdivision) {
      this.submitForm.subdivision = subdivision;
    }
  }

  getMemberPosition() {
    this.gettingMemberPosition = true;
    const data = {
      orgid: this.orgid,
    };
    this.getMemberSub && this.getMemberSub.unsubscribe();
    this.getMemberSub = this.kunyekService.getMemberPosition(data).subscribe(
      (res: any) => {
        if (res.returncode == '300') {
          this.departmentList = this.departmentList.concat(res.departmentlist);
          this.divisionList = this.divisionList.concat(res.divisionlist);
          this.teamidList = this.teamidList.concat(res.teamidlist);
          this.costCenterList = this.costCenterList.concat(res.costcenterlist);
          this.subDivisionList = this.subDivisionList.concat(res.subdivision);
        } else {
          this.messageService.openSnackBar(
            res.message || res.status || 'Server Error',
            'warn'
          );
        }
        this.gettingMemberPosition = false;
      },
      (err) => {
        this.gettingMemberPosition = false;
      }
    );
  }

  searchTextChange() {
    this.currentPage = 1;
  }

  clear() {
    this.searchText = '';
  }

  sortData(sort: Sort) {
    const data = this.timecardList;
    if (!sort.active || sort.direction === '') {
      this.timecardList = data;
      return;
    }
    this.timecardList = data.sort((a: any, b: any) => {
      const isAsc = sort.direction === 'asc';
      if (sort.active == 'employeeid') {
        return this.allinoneService.compare(a.employeeid, b.employeeid, isAsc);
      } else if (sort.active == 'username') {
        return this.allinoneService.compare(a.username, b.username, isAsc);
      } else if (sort.active == 'department') {
        return this.allinoneService.compare(a.department, b.department, isAsc);
      } else if (sort.active == 'division') {
        return this.allinoneService.compare(a.division, b.division, isAsc);
      } else if (sort.active == 'teamid') {
        return this.allinoneService.compare(a.teamid, b.teamid, isAsc);
      } else if (sort.active == 'workingdays') {
        return this.allinoneService.compare(
          a.workingdays,
          b.workingdays,
          isAsc
        );
      } else if (sort.active == 'workinghours') {
        return this.allinoneService.compare(
          a.workinghours,
          b.workinghours,
          isAsc
        );
      } else if (sort.active == 'actualworkingday') {
        return this.allinoneService.compare(
          a.actualworkingday,
          b.actualworkingday,
          isAsc
        );
      } else if (sort.active == 'actualworkinghour') {
        return this.allinoneService.compare(
          a.actualworkinghour,
          b.actualworkinghour,
          isAsc
        );
      } else if (sort.active == 'activitydays') {
        return this.allinoneService.compare(
          a.activitydays,
          b.activitydays,
          isAsc
        );
      } else if (sort.active == 'activityhours') {
        return this.allinoneService.compare(
          a.activityhours,
          b.activityhours,
          isAsc
        );
      } else if (sort.active == 'officecount') {
        return this.allinoneService.compare(
          a.officecount,
          b.officecount,
          isAsc
        );
      } else if (sort.active == 'wfhcount') {
        return this.allinoneService.compare(a.wfhcount, b.wfhcount, isAsc);
      }
      return 0;
    });
  }

  downloadSheet() {
    var exdata: any = [];
    // var date = this.allinoneService.formatDBToShow(this.allinoneService.formatDate(this.submitForm.date));
    // var startdate = this.allinoneService.formatDBToShow(this.allinoneService.formatDate(this.submitForm.startdate));
    // var enddate = this.allinoneService.formatDBToShow(this.allinoneService.formatDate(this.submitForm.enddate));
    // var name = 'Time Card Report (' + startdate + '-' + enddate + ').xlsx'
    const startdate = this.allinoneService.formatDBToShow(
      this.allinoneService.parseDate(this.submitForm.startdate)
    );
    const enddate = this.allinoneService.formatDBToShow(
      this.allinoneService.parseDate(this.submitForm.enddate)
    );
    var name = 'Time Card Report (' + startdate + ' - ' + enddate + ').xlsx';
    // var name = 'Time Card Report.xlsx'
    var filteredData = this.filterPipe.transform(
      this.timecardList,
      this.searchText,
      'timecardreport'
    );

    filteredData.map((item: any) => {
      var temp = {
        'Employee ID': item.employeeid,
        'User ID': item.userid,
        Username: item.username,
        Department: item.department,
        Division: item.division,
        'Team ID': item.teamid,
        'Cost Center': item.costcenter,
        'WP Working Day': item.workingdays,
        'WP Working Hour': item.workinghours,
        'Actual Working Day': item.actualworkingday,
        'Actual Working Hour':
          item.actualworkinghour +
          ' ' +
          '(' +
          item.actualworkingpercentage +
          '%)',
        'Activity Day': item.activitydays,
        'Activity Hour':
          item.activityhours + ' ' + '(' + item.activityhrpercentage + '%)',
        'Office Count': item.officecount,
        'WFH Count': item.wfhcount,
      };
      exdata.push(temp);
    });
    this.allinoneService.exportEcecl(exdata, name);
  }

  changePageCount(event: any) {
    this.itemPerPage = event.target.value;
    this.currentPage = 1;
  }

  // getCurrentAndPreviousYearMonths() {
  //   const currentDate = new Date();
  //   const currentYear = currentDate.getFullYear();
  //   const previousYear = currentYear - 1;

  //   const months = [
  //     { id: '01', name: 'Jan' },
  //     { id: '02', name: 'Feb' },
  //     { id: '03', name: 'Mar' },
  //     { id: '04', name: 'Apr' },
  //     { id: '05', name: 'May' },
  //     { id: '06', name: 'Jun' },
  //     { id: '07', name: 'Jul' },
  //     { id: '08', name: 'Aug' },
  //     { id: '09', name: 'Sep' },
  //     { id: '10', name: 'Oct' },
  //     { id: '11', name: 'Nov' },
  //     { id: '12', name: 'Dec' }
  //   ];

  //   // ***
  //   // this.submitForm.date = currentYear.toString() + months[currentDate.getMonth()].id;

  //   const currentMonths = months.map(month => {
  //     return {
  //       id: currentYear+month.id,
  //       name: month.name,
  //       monthYear: `${month.name} ${currentYear}`
  //     };
  //   });

  //   const previousMonths = months.map(month => {
  //     return {
  //       id: month.id,
  //       name: month.name,
  //       monthYear: `${month.name} ${previousYear}`
  //     };
  //   });

  //   return [...currentMonths, ...previousMonths];
  // }
}
